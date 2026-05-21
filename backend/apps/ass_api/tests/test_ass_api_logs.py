import json

import httpx
import pytest
from django.test import override_settings

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
