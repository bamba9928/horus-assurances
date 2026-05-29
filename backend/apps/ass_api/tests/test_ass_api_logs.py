import json

import httpx
import pytest
from django.test import override_settings
from rest_framework import serializers

from apps.ass_api.applicationtiers import ApplicationTiersPublicClient
from apps.ass_api.client import ASSAPIClient
from apps.ass_api.models import ASSAPICallLog
from apps.ass_api.sanitizers import REDACTED, sanitize_value
from apps.groups.models import PartnerGroup


def serialized(value):
    return json.dumps(value, sort_keys=True)


@pytest.mark.parametrize(
    "payload",
    [
        {
            "username": "ass",
            "password": "very-secret-password",
            "nested": {
                "token": "secret-token",
                "authorization": "Basic abcdef123456",
                "api_key": "wave-api-key",
            },
        },
        {
            "message": "password=very-secret-password token=secret-token secret=abc",
        },
    ],
)
def test_sanitize_value_masks_sensitive_values(payload):
    result = serialized(sanitize_value(payload))

    assert "very-secret-password" not in result
    assert "secret-token" not in result
    assert "wave-api-key" not in result
    assert "abcdef123456" not in result
    assert REDACTED in result


@pytest.mark.parametrize(
    ("method_name", "endpoint"),
    [
        ("calculate_rc", "/api/v1/partner/rc.request"),
        ("calculate_fleet_rc", "/api/v1/partner/rc.flotte.request"),
        ("calculate_trailer_rc", "/api/v1/partner/remorque.rc.request"),
        ("calculate_school_bus_rc", "/api/v1/partner/bus.ecole.rc"),
        ("calculate_garage_rc", "/api/v1/partner/rc.garage"),
        ("calculate_moto_rc", "/api/v1/partner/rc.moto"),
        ("request_qrcode", "/api/v1/partner/qrcode.request"),
        ("request_fleet_qrcode", "/api/v1/partner/qrcode.flotte.request"),
        ("request_trailer_qrcode", "/api/v1/partner/remorque.qrcode.request"),
        ("request_school_bus_qrcode", "/api/v1/partner/bus.ecole.request"),
        ("request_garage_qrcode", "/api/v1/partner/garage.request"),
        ("request_moto_qrcode", "/api/v1/partner/moto.request"),
        ("get_qrcode_stock", "/api/v1/partner/stock.qr"),
        ("cancel_qrcode", "/api/v1/partner/qrcode.cancel"),
        ("check_qrcode_status", "/api/v1/promobile/check.qrcode.status"),
        ("verify_registration", "/api/v1/partner/verif.immatriculation"),
    ],
)
def test_ass_client_partner_methods_use_documented_endpoints(
    method_name,
    endpoint,
    monkeypatch,
):
    calls = []
    client = ASSAPIClient(base_url="https://ass.example.test", username="u", password="p")

    def fake_post(received_endpoint, payload, *, partner_group=None, contract=None):
        calls.append(
            {
                "endpoint": received_endpoint,
                "payload": payload,
                "partner_group": partner_group,
                "contract": contract,
            }
        )
        return {"ok": True}

    monkeypatch.setattr(client, "_post", fake_post)

    result = getattr(client, method_name)({"request": "payload"})

    assert result == {"ok": True}
    assert calls == [
        {
            "endpoint": endpoint,
            "payload": {"request": "payload"},
            "partner_group": None,
            "contract": None,
        }
    ]


def test_applicationtiers_public_client_normalizes_registration_number():
    assert ApplicationTiersPublicClient.normalize_immat(" dk-1234 aa ") == "DK1234AA"
    assert ApplicationTiersPublicClient.normalize_immat("DK 12\u201334") == "DK1234"
    assert ApplicationTiersPublicClient.normalize_immat("") == ""


def test_applicationtiers_public_client_exposes_verify_endpoint():
    client = ApplicationTiersPublicClient(base_url="https://public.example.test")

    endpoints = client.get_public_endpoints()

    assert endpoints == [
        {
            "name": "verify_vehicle_insurance",
            "method": "GET",
            "path": "/applicationtiers/verify/{immatriculation}",
            "summary": (
                "Verifie si une immatriculation a une attestation d'assurance valide."
            ),
            "auth": (
                "Aucune auth requise sur l'endpoint final ; la racine "
                "/applicationtiers est protegee en Basic Auth."
            ),
            "content_type": "application/json",
            "publicly_accessible": True,
        }
    ]


def test_applicationtiers_public_client_verifies_vehicle_success():
    def handler(request):
        assert request.method == "GET"
        assert str(request.url) == "https://public.example.test/verify/DK1234AA"
        assert request.headers["accept"] == "application/json"
        return httpx.Response(
            200,
            json={
                "operationStatus": "SUCCESS",
                "data": {"attestation": "SN001"},
            },
        )

    client = ApplicationTiersPublicClient(
        base_url="https://public.example.test",
        transport=httpx.MockTransport(handler),
    )

    result = client.verify_vehicle("DK-1234-AA")

    assert result["operationStatus"] == "SUCCESS"
    assert result["httpStatus"] == 200
    assert result["queriedImmatriculation"] == "DK1234AA"
    assert result["data"]["attestation"] == "SN001"


def test_applicationtiers_public_client_returns_not_found_payload():
    def handler(request):
        return httpx.Response(404, json={"message": "not found"})

    client = ApplicationTiersPublicClient(
        base_url="https://public.example.test",
        transport=httpx.MockTransport(handler),
    )

    result = client.verify_vehicle("DK 0000 AA")

    assert result == {
        "operationStatus": "NOT_FOUND",
        "operationMessage": "Aucune attestation trouvee pour cette immatriculation.",
        "data": {},
        "httpStatus": 404,
        "queriedImmatriculation": "DK0000AA",
    }


def test_applicationtiers_public_client_rejects_invalid_json():
    def handler(request):
        return httpx.Response(200, content=b"not json")

    client = ApplicationTiersPublicClient(
        base_url="https://public.example.test",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(ValueError, match="Reponse invalide"):
        client.verify_vehicle("DK-1234-AA")


@pytest.mark.django_db
@override_settings(
    ASS_BASE_URL="https://ass.example.test",
    ASS_USERNAME="ass-user",
    ASS_PASSWORD="ass-password-secret",
    ASS_TIMEOUT_SECONDS=5,
)
def test_successful_ass_call_creates_sanitized_log():
    group = PartnerGroup.objects.create(name="ASS Groupe A", slug="ass-groupe-a")

    def handler(request):
        assert request.headers["authorization"].startswith("Basic ")
        return httpx.Response(
            200,
            json={
                "ok": True,
                "token": "response-token-secret",
                "password": "response-password-secret",
            },
        )

    client = ASSAPIClient(transport=httpx.MockTransport(handler))

    result = client.calculate_rc(
        {
            "puissanceFiscale": 8,
            "password": "request-password-secret",
            "authorization": "Basic request-auth-secret",
        },
        partner_group=group,
    )

    log = ASSAPICallLog.objects.get()
    serialized_log = serialized(
        {
            "request_payload": log.request_payload,
            "response_payload": log.response_payload,
            "error_message": log.error_message,
        }
    )
    assert result["ok"] is True
    assert log.partner_group == group
    assert log.endpoint == "/api/v1/partner/rc.request"
    assert log.status == ASSAPICallLog.Status.SUCCESS
    assert log.http_status_code == 200
    assert "ass-user" not in serialized_log
    assert "ass-password-secret" not in serialized_log
    assert "request-password-secret" not in serialized_log
    assert "request-auth-secret" not in serialized_log
    assert "response-token-secret" not in serialized_log
    assert "response-password-secret" not in serialized_log
    assert REDACTED in serialized_log


@pytest.mark.django_db
@override_settings(
    ASS_BASE_URL="https://ass.example.test",
    ASS_USERNAME="ass-user",
    ASS_PASSWORD="ass-password-secret",
    ASS_TIMEOUT_SECONDS=5,
)
def test_failed_ass_call_creates_sanitized_log():
    group = PartnerGroup.objects.create(name="ASS Groupe B", slug="ass-groupe-b")

    def handler(request):
        return httpx.Response(
            500,
            json={
                "error": "upstream failure",
                "password": "response-password-secret",
                "token": "response-token-secret",
            },
        )

    client = ASSAPIClient(transport=httpx.MockTransport(handler))

    with pytest.raises(httpx.HTTPStatusError):
        client.request_qrcode(
            {
                "referenceTrxPartner": "trx-001",
                "secret": "request-secret",
                "api_key": "request-api-key",
            },
            partner_group=group,
        )

    log = ASSAPICallLog.objects.get()
    serialized_log = serialized(
        {
            "request_payload": log.request_payload,
            "response_payload": log.response_payload,
            "error_message": log.error_message,
        }
    )
    assert log.partner_group == group
    assert log.endpoint == "/api/v1/partner/qrcode.request"
    assert log.status == ASSAPICallLog.Status.ERROR
    assert log.http_status_code == 500
    assert "ass-user" not in serialized_log
    assert "ass-password-secret" not in serialized_log
    assert "request-secret" not in serialized_log
    assert "request-api-key" not in serialized_log
    assert "response-password-secret" not in serialized_log
    assert "response-token-secret" not in serialized_log
    assert REDACTED in serialized_log


@pytest.mark.django_db
@override_settings(
    ASS_BASE_URL="https://ass.example.test",
    ASS_USERNAME="ass-user",
    ASS_PASSWORD="ass-password-secret",
    ASS_TIMEOUT_SECONDS=5,
)
def test_ass_business_error_response_creates_error_log():
    group = PartnerGroup.objects.create(name="ASS Groupe C", slug="ass-groupe-c")

    def handler(request):
        return httpx.Response(
            200,
            json={
                "operationStatus": "ERROR",
                "operationMessage": "Mot de passe password=response-password-secret",
            },
        )

    client = ASSAPIClient(transport=httpx.MockTransport(handler))

    with pytest.raises(serializers.ValidationError):
        client.calculate_rc(
            {
                "puissanceFiscale": 8,
                "password": "request-password-secret",
            },
            partner_group=group,
        )

    log = ASSAPICallLog.objects.get()
    serialized_log = serialized(
        {
            "request_payload": log.request_payload,
            "response_payload": log.response_payload,
            "error_message": log.error_message,
        }
    )
    assert log.partner_group == group
    assert log.endpoint == "/api/v1/partner/rc.request"
    assert log.status == ASSAPICallLog.Status.ERROR
    assert log.http_status_code == 200
    assert "ass-password-secret" not in serialized_log
    assert "request-password-secret" not in serialized_log
    assert "response-password-secret" not in serialized_log
    assert REDACTED in serialized_log


@pytest.mark.django_db
def test_log_model_sanitizes_payloads_on_save():
    ASSAPICallLog.objects.create(
        endpoint="/api/v1/partner/test",
        method="POST",
        status=ASSAPICallLog.Status.ERROR,
        request_payload={"password": "raw-password", "safe": "visible"},
        response_payload={"authorization": "Basic raw-auth"},
        error_message="token=raw-token password=raw-password",
    )

    log = ASSAPICallLog.objects.get()
    serialized_log = serialized(
        {
            "request_payload": log.request_payload,
            "response_payload": log.response_payload,
            "error_message": log.error_message,
        }
    )
    assert "raw-password" not in serialized_log
    assert "raw-auth" not in serialized_log
    assert "raw-token" not in serialized_log
    assert log.request_payload["safe"] == "visible"
    assert REDACTED in serialized_log
