import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import datetime, timezone as datetime_timezone
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import serializers

from apps.ass_api.sanitizers import sanitize_error_message, sanitize_value

from .models import Payment, PaymentWebhookEvent
from .services import confirm_payment


class WebhookConfigurationError(Exception):
    pass


class WebhookSignatureError(Exception):
    pass


class WebhookProcessingError(Exception):
    pass


@dataclass(frozen=True)
class WebhookResult:
    event: PaymentWebhookEvent
    duplicate: bool = False


SUCCESS_VALUES = {
    "checkout.session.completed",
    "completed",
    "confirmed",
    "paid",
    "success",
    "successful",
    "succeeded",
}
FAILED_VALUES = {
    "checkout.session.cancelled",
    "checkout.session.expired",
    "checkout.session.payment_failed",
    "cancelled",
    "canceled",
    "error",
    "expired",
    "failed",
}
REFERENCE_KEYS = (
    "external_reference",
    "externalReference",
    "client_reference",
    "clientReference",
    "merchant_reference",
    "merchantReference",
    "order_id",
    "orderId",
    "payment_reference",
    "paymentReference",
    "reference",
    "referenceTrxPartner",
    "transaction_id",
    "transactionId",
    "txnid",
    "txn_id",
    "pay_token",
    "checkout_session_id",
    "checkoutSessionId",
)
AMOUNT_KEYS = (
    "amount",
    "amount_total",
    "amountTotal",
    "total_amount",
    "totalAmount",
)
CURRENCY_KEYS = ("currency", "currency_code", "currencyCode")


def process_wave_webhook(*, raw_body: bytes, headers) -> WebhookResult:
    payload = _decode_json(raw_body)
    _verify_wave_signature(raw_body=raw_body, headers=headers)
    return _process_verified_webhook(
        provider=PaymentWebhookEvent.Provider.WAVE,
        payload=payload,
        headers=headers,
        fallback_event_id=_extract_event_id(payload),
    )


def process_orange_money_webhook(*, raw_body: bytes, headers) -> WebhookResult:
    payload = _decode_json(raw_body)
    _verify_orange_money_signature(headers=headers)
    return _process_verified_webhook(
        provider=PaymentWebhookEvent.Provider.ORANGE_MONEY,
        payload=payload,
        headers=headers,
        fallback_event_id=_get_header(headers, "x-correlation-id"),
    )


def _decode_json(raw_body: bytes):
    try:
        return json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise WebhookProcessingError("Payload JSON invalide.") from exc


def _verify_wave_signature(*, raw_body: bytes, headers):
    secret = settings.WAVE_WEBHOOK_SECRET
    if not secret:
        raise WebhookConfigurationError("WAVE_WEBHOOK_SECRET est obligatoire.")

    signature_header = _get_header(headers, "Wave-Signature")
    if not signature_header:
        raise WebhookSignatureError("Signature Wave manquante.")

    parts = _parse_comma_header(signature_header)
    timestamp = parts.get("t")
    signatures = parts.get("v1", [])
    if not timestamp or not signatures:
        raise WebhookSignatureError("Format de signature Wave invalide.")
    _validate_unix_timestamp(timestamp)

    signed_payload = timestamp.encode("utf-8") + raw_body
    expected_signature = hmac.new(
        secret.encode("utf-8"),
        signed_payload,
        hashlib.sha256,
    ).hexdigest()
    if not any(hmac.compare_digest(expected_signature, value) for value in signatures):
        raise WebhookSignatureError("Signature Wave invalide.")


def _verify_orange_money_signature(*, headers):
    secret = settings.ORANGE_MONEY_WEBHOOK_SECRET
    if not secret:
        raise WebhookConfigurationError("ORANGE_MONEY_WEBHOOK_SECRET est obligatoire.")

    correlation_id = _get_header(headers, "x-correlation-id")
    request_date = _get_header(headers, "x-request-date")
    digest = _get_header(headers, "digest")
    if not correlation_id or not request_date or not digest:
        raise WebhookSignatureError("Headers de signature Orange Money manquants.")

    _validate_request_date(request_date)
    signature = _parse_digest_signature(digest)
    signed_payload = f"{correlation_id}{request_date}".encode("utf-8")
    expected_signature = hmac.new(
        secret.encode("utf-8"),
        signed_payload,
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected_signature, signature):
        raise WebhookSignatureError("Signature Orange Money invalide.")


def _validate_unix_timestamp(timestamp):
    try:
        signed_at = datetime.fromtimestamp(int(timestamp), tz=datetime_timezone.utc)
    except (ValueError, OSError) as exc:
        raise WebhookSignatureError("Timestamp de signature invalide.") from exc
    _validate_timestamp_tolerance(signed_at)


def _validate_request_date(request_date):
    signed_at = parse_datetime(request_date)
    if signed_at is None:
        raise WebhookSignatureError("Date de signature invalide.")
    if timezone.is_naive(signed_at):
        signed_at = timezone.make_aware(signed_at, datetime_timezone.utc)
    _validate_timestamp_tolerance(signed_at)


def _validate_timestamp_tolerance(signed_at):
    now = timezone.now()
    tolerance = settings.PAYMENT_WEBHOOK_TIMESTAMP_TOLERANCE_SECONDS
    age_seconds = abs((now - signed_at).total_seconds())
    if age_seconds > tolerance:
        raise WebhookSignatureError("Signature expiree ou datee du futur.")


def _parse_comma_header(value):
    parsed = {}
    for part in value.split(","):
        if "=" not in part:
            continue
        key, nested_value = part.split("=", 1)
        parsed.setdefault(key.strip(), []).append(nested_value.strip())
    return {key: values[0] if key == "t" else values for key, values in parsed.items()}


def _parse_digest_signature(digest):
    for part in digest.replace(",", "&").split("&"):
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        if key.strip().lower() == "signature":
            return value.strip()
    raise WebhookSignatureError("Signature Orange Money absente du digest.")


def _process_verified_webhook(*, provider, payload, headers, fallback_event_id):
    event_id = _extract_event_id(payload) or fallback_event_id
    if not event_id:
        raise WebhookProcessingError("Identifiant d'evenement webhook manquant.")

    result = None
    caught_exception = None
    with transaction.atomic():
        event, created = PaymentWebhookEvent.objects.select_for_update().get_or_create(
            provider=provider,
            event_id=str(event_id),
            defaults={
                "event_type": _extract_event_type(payload),
                "provider_reference": _first_value(payload, REFERENCE_KEYS) or "",
                "payload": sanitize_value(payload),
                "headers": sanitize_value(_safe_headers(headers)),
            },
        )
        if not created and event.status in (
            PaymentWebhookEvent.Status.PROCESSED,
            PaymentWebhookEvent.Status.IGNORED,
        ):
            return WebhookResult(event=event, duplicate=True)

        event.event_type = event.event_type or _extract_event_type(payload)
        event.provider_reference = event.provider_reference or (
            _first_value(payload, REFERENCE_KEYS) or ""
        )
        event.payload = sanitize_value(payload)
        event.headers = sanitize_value(_safe_headers(headers))
        event.status = PaymentWebhookEvent.Status.RECEIVED
        event.error_message = ""
        event.save(
            update_fields=[
                "event_type",
                "provider_reference",
                "payload",
                "headers",
                "status",
                "error_message",
            ]
        )

        try:
            payment = _find_payment(provider=provider, payload=payload)
            _validate_payment_payload(payment=payment, payload=payload)
            target_status = _target_payment_status(payload)
            if target_status is None:
                event.status = PaymentWebhookEvent.Status.IGNORED
                event.payment = payment
                event.processed_at = timezone.now()
                event.save(update_fields=["status", "payment", "processed_at"])
                result = WebhookResult(event=event, duplicate=False)
                return result

            if target_status == Payment.Status.CONFIRMED:
                payment = confirm_payment(
                    payment=payment,
                    idempotency_key=f"webhook:{provider}:{event.event_id}",
                )
            else:
                payment = _mark_payment_terminal(payment=payment, status=target_status)

            event.payment = payment
            event.status = PaymentWebhookEvent.Status.PROCESSED
            event.processed_at = timezone.now()
            event.save(update_fields=["payment", "status", "processed_at"])
            result = WebhookResult(event=event, duplicate=False)
        except Exception as exc:
            event.status = PaymentWebhookEvent.Status.FAILED
            event.error_message = sanitize_error_message(str(exc))
            event.processed_at = timezone.now()
            event.save(update_fields=["status", "error_message", "processed_at"])
            caught_exception = exc

    if caught_exception:
        raise caught_exception
    return result


def _find_payment(*, provider, payload):
    method = (
        Payment.Method.WAVE
        if provider == PaymentWebhookEvent.Provider.WAVE
        else Payment.Method.ORANGE_MONEY
    )
    references = _all_values(payload, REFERENCE_KEYS)
    if not references:
        raise WebhookProcessingError("Reference paiement introuvable dans le webhook.")

    query = Payment.objects.select_for_update().filter(method=method)
    payment = query.filter(external_reference__in=references).first()
    if payment:
        return payment
    payment = query.filter(idempotency_key__in=references).first()
    if payment:
        return payment
    raise WebhookProcessingError("Paiement introuvable pour ce webhook.")


def _validate_payment_payload(*, payment, payload):
    amount = _extract_decimal(payload, AMOUNT_KEYS)
    if amount is not None and amount != payment.amount:
        raise serializers.ValidationError(
            {"amount": "Le montant webhook ne correspond pas au paiement."}
        )

    currency = _first_value(payload, CURRENCY_KEYS)
    if currency and str(currency).upper() != payment.currency:
        raise serializers.ValidationError(
            {"currency": "La devise webhook ne correspond pas au paiement."}
        )


def _target_payment_status(payload):
    values = {
        str(value).strip().lower()
        for value in _all_values(payload, ("type", "event_type", "eventType", "status", "state"))
        if value not in (None, "")
    }
    if values & SUCCESS_VALUES:
        return Payment.Status.CONFIRMED
    if values & {"cancelled", "canceled", "expired", "checkout.session.cancelled", "checkout.session.expired"}:
        return Payment.Status.CANCELLED
    if values & FAILED_VALUES:
        return Payment.Status.FAILED
    return None


def _mark_payment_terminal(*, payment, status):
    payment = Payment.objects.select_for_update().get(pk=payment.pk)
    if payment.status == status:
        return payment
    if payment.status == Payment.Status.CONFIRMED:
        return payment
    if payment.status != Payment.Status.PENDING:
        return payment
    payment.status = status
    payment.full_clean()
    payment.save(update_fields=["status", "updated_at"])
    return payment


def _extract_event_id(payload):
    return _first_value(
        payload,
        ("event_id", "eventId", "webhook_id", "webhookId", "id"),
        prefer_top_level=True,
    )


def _extract_event_type(payload):
    return str(_first_value(payload, ("type", "event_type", "eventType")) or "")


def _extract_decimal(payload, keys):
    value = _first_value(payload, keys)
    if value in (None, ""):
        return None
    try:
        return Decimal(str(value).replace(" ", "").replace(",", ".")).quantize(
            Decimal("0.01")
        )
    except (InvalidOperation, ValueError) as exc:
        raise serializers.ValidationError(
            {"amount": "Le montant webhook est invalide."}
        ) from exc


def _first_value(value, keys, *, prefer_top_level=False):
    values = _all_values(value, keys, prefer_top_level=prefer_top_level)
    return values[0] if values else None


def _all_values(value, keys, *, prefer_top_level=False):
    normalized_keys = {_normalize_key(key) for key in keys}
    values = []

    if isinstance(value, dict):
        items = value.items()
        for key, nested_value in items:
            if _normalize_key(key) in normalized_keys and nested_value not in (None, ""):
                values.append(nested_value)
        if prefer_top_level and values:
            return [str(item) for item in values]
        for nested_value in value.values():
            values.extend(_all_values(nested_value, keys))

    if isinstance(value, list):
        for item in value:
            values.extend(_all_values(item, keys))

    deduped = []
    for item in values:
        normalized_value = str(item)
        if normalized_value not in deduped:
            deduped.append(normalized_value)
    return deduped


def _normalize_key(key):
    return str(key).strip().replace("_", "").replace("-", "").lower()


def _get_header(headers, name):
    try:
        return headers.get(name) or headers.get(name.lower()) or headers.get(name.upper())
    except AttributeError:
        normalized_name = name.lower()
        for key, value in headers.items():
            if str(key).lower() == normalized_name:
                return value
    return None


def _safe_headers(headers):
    return {
        key: value
        for key, value in dict(headers).items()
        if str(key).lower()
        in {
            "digest",
            "wave-signature",
            "x-correlation-id",
            "x-request-date",
            "user-agent",
            "content-type",
        }
    }
