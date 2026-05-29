import logging
import re
from dataclasses import asdict, dataclass
from typing import Any
from urllib.parse import quote

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PublicEndpoint:
    name: str
    method: str
    path: str
    summary: str
    auth: str
    content_type: str
    publicly_accessible: bool


PUBLIC_ENDPOINTS = (
    PublicEndpoint(
        name="verify_vehicle_insurance",
        method="GET",
        path="/applicationtiers/verify/{immatriculation}",
        summary="Verifie si une immatriculation a une attestation d'assurance valide.",
        auth=(
            "Aucune auth requise sur l'endpoint final ; la racine "
            "/applicationtiers est protegee en Basic Auth."
        ),
        content_type="application/json",
        publicly_accessible=True,
    ),
)


class ApplicationTiersPublicClient:
    DEFAULT_BASE_URL = "https://apiaas.diotali.com/applicationtiers"
    DEFAULT_CONNECT_TIMEOUT_SECONDS = 5
    DEFAULT_READ_TIMEOUT_SECONDS = 15

    def __init__(self, *, base_url=None, timeout=None, transport=None):
        configured_base_url = base_url or getattr(
            settings,
            "AAS_PUBLIC_BASE_URL",
            self.DEFAULT_BASE_URL,
        )
        self.base_url = str(configured_base_url).rstrip("/")
        self.timeout = self._coerce_timeout(timeout)
        self.transport = transport
        self.headers = {
            "Accept": "application/json",
            "User-Agent": "horus-assurances/1.0",
        }

    @staticmethod
    def normalize_immat(value):
        if not value or not isinstance(value, str):
            return ""
        return re.sub(r"[\s\-\u2013\u2014]+", "", value.strip().upper())

    def get_public_endpoints(self):
        return [asdict(endpoint) for endpoint in PUBLIC_ENDPOINTS]

    def verify_vehicle(self, immatriculation):
        immat_clean = self.normalize_immat(immatriculation)
        if not immat_clean:
            raise ValueError("immatriculation requise")

        url = f"{self.base_url}/verify/{quote(immat_clean, safe='')}"
        with httpx.Client(
            timeout=self.timeout,
            transport=self.transport,
            headers=self.headers,
        ) as client:
            response = client.get(url)

        if response.status_code == 404:
            return {
                "operationStatus": "NOT_FOUND",
                "operationMessage": (
                    "Aucune attestation trouvee pour cette immatriculation."
                ),
                "data": {},
                "httpStatus": 404,
                "queriedImmatriculation": immat_clean,
            }

        response.raise_for_status()
        try:
            payload = response.json()
        except ValueError as exc:
            logger.error(
                "ApplicationTiers verify a retourne un JSON invalide pour %s",
                immat_clean,
            )
            raise ValueError("Reponse invalide de l'API ApplicationTiers") from exc

        if isinstance(payload, dict):
            payload.setdefault("httpStatus", response.status_code)
            payload.setdefault("queriedImmatriculation", immat_clean)
            return payload

        raise ValueError("Reponse inattendue de l'API ApplicationTiers")

    def _coerce_timeout(self, timeout):
        if timeout is not None:
            if isinstance(timeout, tuple):
                return httpx.Timeout(timeout[1], connect=timeout[0])
            return timeout
        read_timeout = getattr(
            settings,
            "AAS_PUBLIC_TIMEOUT_SECONDS",
            self.DEFAULT_READ_TIMEOUT_SECONDS,
        )
        return httpx.Timeout(
            read_timeout,
            connect=self.DEFAULT_CONNECT_TIMEOUT_SECONDS,
        )


applicationtiers_public_client = ApplicationTiersPublicClient()


def get_applicationtiers_public_endpoints():
    return applicationtiers_public_client.get_public_endpoints()
