import time
from urllib.parse import urljoin

import httpx
from django.conf import settings
from rest_framework import serializers

from .models import ASSAPICallLog
from .sanitizers import sanitize_error_message, sanitize_value


class ASSAPIClient:
    def __init__(
        self,
        *,
        base_url=None,
        username=None,
        password=None,
        timeout=None,
        transport=None,
    ):
        self.base_url = (base_url if base_url is not None else settings.ASS_BASE_URL).rstrip("/")
        self.username = username if username is not None else settings.ASS_USERNAME
        self.password = password if password is not None else settings.ASS_PASSWORD
        self.timeout = timeout if timeout is not None else settings.ASS_TIMEOUT_SECONDS
        self.transport = transport

    def calculate_rc(self, payload, *, partner_group=None, contract=None):
        return self._post(
            "/api/v1/partner/rc.request",
            payload,
            partner_group=partner_group,
            contract=contract,
        )

    def request_qrcode(self, payload, *, partner_group=None, contract=None):
        return self._post(
            "/api/v1/partner/qrcode.request",
            payload,
            partner_group=partner_group,
            contract=contract,
        )

    def verify_registration(self, payload, *, partner_group=None, contract=None):
        return self._post(
            "/api/v1/partner/verif.immatriculation",
            payload,
            partner_group=partner_group,
            contract=contract,
        )

    def _post(self, endpoint, payload, *, partner_group=None, contract=None):
        if not self.base_url:
            raise serializers.ValidationError({"ASS_BASE_URL": "ASS_BASE_URL est obligatoire."})
        if not self.username or not self.password:
            raise serializers.ValidationError(
                {"ASS_AUTH": "Les identifiants ASS doivent etre configures."}
            )

        url = urljoin(f"{self.base_url}/", endpoint.lstrip("/"))
        started_at = time.perf_counter()
        response_payload = {}
        http_status_code = None

        try:
            with httpx.Client(
                auth=(self.username, self.password),
                timeout=self.timeout,
                transport=self.transport,
            ) as client:
                response = client.post(url, json=payload)
                http_status_code = response.status_code
                response.raise_for_status()
                response_payload = self._safe_response_json(response)
        except httpx.HTTPError as exc:
            duration_ms = self._duration_ms(started_at)
            response = getattr(exc, "response", None)
            if response is not None:
                http_status_code = response.status_code
                response_payload = self._safe_response_json(response)
            self._log_call(
                partner_group=partner_group,
                contract=contract,
                endpoint=endpoint,
                status=ASSAPICallLog.Status.ERROR,
                http_status_code=http_status_code,
                request_payload=payload,
                response_payload=response_payload,
                error_message=sanitize_error_message(str(exc)),
                duration_ms=duration_ms,
            )
            raise

        duration_ms = self._duration_ms(started_at)
        self._log_call(
            partner_group=partner_group,
            contract=contract,
            endpoint=endpoint,
            status=ASSAPICallLog.Status.SUCCESS,
            http_status_code=http_status_code,
            request_payload=payload,
            response_payload=response_payload,
            error_message="",
            duration_ms=duration_ms,
        )
        return response_payload

    def _log_call(
        self,
        *,
        partner_group,
        contract,
        endpoint,
        status,
        http_status_code,
        request_payload,
        response_payload,
        error_message,
        duration_ms,
    ):
        ASSAPICallLog.objects.create(
            partner_group=partner_group,
            contract=contract,
            endpoint=endpoint,
            method="POST",
            status=status,
            http_status_code=http_status_code,
            request_payload=sanitize_value(request_payload),
            response_payload=sanitize_value(response_payload),
            error_message=sanitize_error_message(error_message),
            duration_ms=duration_ms,
        )

    @staticmethod
    def _safe_response_json(response):
        try:
            return response.json()
        except ValueError:
            return {"raw": response.text}

    @staticmethod
    def _duration_ms(started_at):
        return max(0, int((time.perf_counter() - started_at) * 1000))
