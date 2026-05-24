import hashlib
import hmac
import json
from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.clients.models import Client
from apps.groups.models import PartnerGroup
from apps.payments.models import Payment, PaymentWebhookEvent
from apps.quotes.models import Quote
from apps.vehicles.models import Vehicle

User = get_user_model()


@pytest.fixture
def webhook_payment_context():
    group = PartnerGroup.objects.create(name="Webhook Groupe", slug="webhook-group")
    contributor = User.objects.create_user(
        username="webhook-apporteur",
        password="password",
        role=User.Role.CONTRIBUTOR,
        partner_group=group,
    )
    client = Client.objects.create(
        partner_group=group,
        contributor=contributor,
        created_by=contributor,
        first_name="Webhook",
        last_name="Client",
        phone="770000001",
    )
    vehicle = Vehicle.objects.create(
        partner_group=group,
        client=client,
        contributor=contributor,
        created_by=contributor,
        registration_number="DK-WEB-001",
        brand="Toyota",
        model="Yaris",
        genre="VP",
        energy=Vehicle.Energy.GASOLINE,
    )
    quote = Quote.objects.create(
        partner_group=group,
        client=client,
        vehicle=vehicle,
        contributor=contributor,
        created_by=contributor,
        premium_amount=Decimal("10000.00"),
        fees_amount=Decimal("1000.00"),
        total_amount=Decimal("11000.00"),
    )
    wave_payment = Payment.objects.create(
        partner_group=group,
        quote=quote,
        client=client,
        contributor=contributor,
        created_by=contributor,
        method=Payment.Method.WAVE,
        amount=quote.total_amount,
        external_reference="wave-checkout-001",
    )
    orange_payment = Payment.objects.create(
        partner_group=group,
        quote=quote,
        client=client,
        contributor=contributor,
        created_by=contributor,
        method=Payment.Method.ORANGE_MONEY,
        amount=quote.total_amount,
        external_reference="orange-order-001",
    )
    return {
        "wave_payment": wave_payment,
        "orange_payment": orange_payment,
    }


def _json_body(payload):
    return json.dumps(payload, separators=(",", ":")).encode("utf-8")


def _wave_signature(body, secret, timestamp=None):
    timestamp = timestamp or int(timezone.now().timestamp())
    digest = hmac.new(
        secret.encode("utf-8"),
        str(timestamp).encode("utf-8") + body,
        hashlib.sha256,
    ).hexdigest()
    return f"t={timestamp},v1={digest}"


def _orange_digest(correlation_id, request_date, secret):
    digest = hmac.new(
        secret.encode("utf-8"),
        f"{correlation_id}{request_date}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return (
        "HMAC-SHA256 SignedHeaders=x-correlation-id;x-request-date"
        f"&Signature={digest}"
    )


@pytest.mark.django_db
@override_settings(
    WAVE_WEBHOOK_SECRET="wave-test-secret",
    PAYMENT_WEBHOOK_TIMESTAMP_TOLERANCE_SECONDS=300,
)
def test_wave_webhook_confirms_payment(webhook_payment_context):
    body = _json_body(
        {
            "id": "wave-event-001",
            "type": "checkout.session.completed",
            "data": {
                "transaction_id": "wave-checkout-001",
                "amount": "11000.00",
                "currency": "XOF",
            },
        }
    )
    client = APIClient()

    response = client.post(
        "/api/v1/webhooks/wave/",
        data=body,
        content_type="application/json",
        HTTP_WAVE_SIGNATURE=_wave_signature(body, "wave-test-secret"),
    )

    webhook_payment_context["wave_payment"].refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert webhook_payment_context["wave_payment"].status == Payment.Status.CONFIRMED
    event = PaymentWebhookEvent.objects.get(event_id="wave-event-001")
    assert event.provider == PaymentWebhookEvent.Provider.WAVE
    assert event.status == PaymentWebhookEvent.Status.PROCESSED
    assert event.payment == webhook_payment_context["wave_payment"]


@pytest.mark.django_db
@override_settings(
    WAVE_WEBHOOK_SECRET="wave-test-secret",
    PAYMENT_WEBHOOK_TIMESTAMP_TOLERANCE_SECONDS=300,
)
def test_wave_webhook_is_idempotent(webhook_payment_context):
    body = _json_body(
        {
            "id": "wave-event-duplicate",
            "type": "checkout.session.completed",
            "data": {
                "transaction_id": "wave-checkout-001",
                "amount": "11000.00",
                "currency": "XOF",
            },
        }
    )
    signature = _wave_signature(body, "wave-test-secret")
    client = APIClient()

    first_response = client.post(
        "/api/v1/webhooks/wave/",
        data=body,
        content_type="application/json",
        HTTP_WAVE_SIGNATURE=signature,
    )
    second_response = client.post(
        "/api/v1/webhooks/wave/",
        data=body,
        content_type="application/json",
        HTTP_WAVE_SIGNATURE=signature,
    )

    assert first_response.status_code == status.HTTP_200_OK
    assert second_response.status_code == status.HTTP_200_OK
    assert second_response.data["status"] == "duplicate"
    assert PaymentWebhookEvent.objects.filter(event_id="wave-event-duplicate").count() == 1


@pytest.mark.django_db
@override_settings(
    WAVE_WEBHOOK_SECRET="wave-test-secret",
    PAYMENT_WEBHOOK_TIMESTAMP_TOLERANCE_SECONDS=300,
)
def test_wave_webhook_rejects_invalid_signature(webhook_payment_context):
    body = _json_body(
        {
            "id": "wave-event-invalid",
            "type": "checkout.session.completed",
            "data": {"transaction_id": "wave-checkout-001"},
        }
    )
    client = APIClient()

    response = client.post(
        "/api/v1/webhooks/wave/",
        data=body,
        content_type="application/json",
        HTTP_WAVE_SIGNATURE="t=1000,v1=bad",
    )

    webhook_payment_context["wave_payment"].refresh_from_db()
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert webhook_payment_context["wave_payment"].status == Payment.Status.PENDING
    assert PaymentWebhookEvent.objects.filter(event_id="wave-event-invalid").count() == 0


@pytest.mark.django_db
@override_settings(
    WAVE_WEBHOOK_SECRET="wave-test-secret",
    PAYMENT_WEBHOOK_TIMESTAMP_TOLERANCE_SECONDS=300,
)
def test_wave_webhook_rejects_replayed_timestamp(webhook_payment_context):
    body = _json_body(
        {
            "id": "wave-event-replay",
            "type": "checkout.session.completed",
            "data": {"transaction_id": "wave-checkout-001"},
        }
    )
    stale_timestamp = int((timezone.now() - timedelta(hours=1)).timestamp())
    client = APIClient()

    response = client.post(
        "/api/v1/webhooks/wave/",
        data=body,
        content_type="application/json",
        HTTP_WAVE_SIGNATURE=_wave_signature(
            body,
            "wave-test-secret",
            timestamp=stale_timestamp,
        ),
    )

    webhook_payment_context["wave_payment"].refresh_from_db()
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert webhook_payment_context["wave_payment"].status == Payment.Status.PENDING


@pytest.mark.django_db
@override_settings(
    WAVE_WEBHOOK_SECRET="wave-test-secret",
    PAYMENT_WEBHOOK_TIMESTAMP_TOLERANCE_SECONDS=300,
)
def test_wave_webhook_rejects_amount_mismatch(webhook_payment_context):
    body = _json_body(
        {
            "id": "wave-event-bad-amount",
            "type": "checkout.session.completed",
            "data": {
                "transaction_id": "wave-checkout-001",
                "amount": "12000.00",
                "currency": "XOF",
            },
        }
    )
    client = APIClient()

    response = client.post(
        "/api/v1/webhooks/wave/",
        data=body,
        content_type="application/json",
        HTTP_WAVE_SIGNATURE=_wave_signature(body, "wave-test-secret"),
    )

    webhook_payment_context["wave_payment"].refresh_from_db()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert webhook_payment_context["wave_payment"].status == Payment.Status.PENDING
    event = PaymentWebhookEvent.objects.get(event_id="wave-event-bad-amount")
    assert event.status == PaymentWebhookEvent.Status.FAILED


@pytest.mark.django_db
@override_settings(
    WAVE_WEBHOOK_SECRET="wave-test-secret",
    PAYMENT_WEBHOOK_TIMESTAMP_TOLERANCE_SECONDS=300,
)
def test_wave_failed_webhook_marks_payment_failed(webhook_payment_context):
    body = _json_body(
        {
            "id": "wave-event-failed",
            "type": "checkout.session.payment_failed",
            "data": {
                "transaction_id": "wave-checkout-001",
                "amount": "11000.00",
                "currency": "XOF",
            },
        }
    )
    client = APIClient()

    response = client.post(
        "/api/v1/webhooks/wave/",
        data=body,
        content_type="application/json",
        HTTP_WAVE_SIGNATURE=_wave_signature(body, "wave-test-secret"),
    )

    webhook_payment_context["wave_payment"].refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert webhook_payment_context["wave_payment"].status == Payment.Status.FAILED


@pytest.mark.django_db
@override_settings(
    ORANGE_MONEY_WEBHOOK_SECRET="orange-test-secret",
    PAYMENT_WEBHOOK_TIMESTAMP_TOLERANCE_SECONDS=300,
)
def test_orange_money_webhook_confirms_payment(webhook_payment_context):
    body = _json_body(
        {
            "eventId": "orange-event-001",
            "status": "SUCCESS",
            "order_id": "orange-order-001",
            "amount": "11000.00",
            "currency": "XOF",
        }
    )
    correlation_id = "orange-correlation-001"
    request_date = timezone.now().isoformat().replace("+00:00", "Z")
    client = APIClient()

    response = client.post(
        "/api/v1/webhooks/orange-money/",
        data=body,
        content_type="application/json",
        HTTP_X_CORRELATION_ID=correlation_id,
        HTTP_X_REQUEST_DATE=request_date,
        HTTP_DIGEST=_orange_digest(
            correlation_id,
            request_date,
            "orange-test-secret",
        ),
    )

    webhook_payment_context["orange_payment"].refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert webhook_payment_context["orange_payment"].status == Payment.Status.CONFIRMED
    event = PaymentWebhookEvent.objects.get(event_id="orange-event-001")
    assert event.provider == PaymentWebhookEvent.Provider.ORANGE_MONEY
    assert event.status == PaymentWebhookEvent.Status.PROCESSED


@pytest.mark.django_db
@override_settings(
    ORANGE_MONEY_WEBHOOK_SECRET="orange-test-secret",
    PAYMENT_WEBHOOK_TIMESTAMP_TOLERANCE_SECONDS=300,
)
def test_orange_money_webhook_rejects_invalid_digest(webhook_payment_context):
    body = _json_body(
        {
            "eventId": "orange-event-invalid",
            "status": "SUCCESS",
            "order_id": "orange-order-001",
        }
    )
    client = APIClient()

    response = client.post(
        "/api/v1/webhooks/orange-money/",
        data=body,
        content_type="application/json",
        HTTP_X_CORRELATION_ID="orange-correlation-invalid",
        HTTP_X_REQUEST_DATE=timezone.now().isoformat().replace("+00:00", "Z"),
        HTTP_DIGEST="HMAC-SHA256 SignedHeaders=x-correlation-id;x-request-date&Signature=bad",
    )

    webhook_payment_context["orange_payment"].refresh_from_db()
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert webhook_payment_context["orange_payment"].status == Payment.Status.PENDING
