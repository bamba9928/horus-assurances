import hashlib
import hmac
import secrets
from datetime import timedelta
from urllib.parse import urlencode

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework import exceptions

from apps.audit.models import AuditLog
from apps.audit.services import record_audit_event

from .models import ClientAccessOtp, ClientAccessToken

TOKEN_PREFIX = "hca_"
OTP_HEADER = "X-Client-OTP"


@transaction.atomic
def create_client_access_token(
    *,
    client,
    contract,
    created_by=None,
    delivery_channel=ClientAccessToken.DeliveryChannel.MANUAL,
    expires_in_days=None,
    rotated_from=None,
):
    expires_in_days = expires_in_days or settings.CLIENT_ACCESS_TOKEN_TTL_DAYS
    raw_token = generate_raw_client_access_token()
    access_token = ClientAccessToken(
        partner_group=client.partner_group,
        client=client,
        contract=contract,
        token_hash=hash_client_access_token(raw_token),
        delivery_channel=delivery_channel,
        created_by=created_by,
        rotated_from=rotated_from,
        expires_at=timezone.now() + timedelta(days=expires_in_days),
    )
    access_token.full_clean()
    access_token.save()
    record_audit_event(
        action=AuditLog.Action.CLIENT_ACCESS_TOKEN_CREATED,
        partner_group=access_token.partner_group,
        actor=created_by,
        target=access_token,
        metadata=_audit_metadata(access_token),
    )
    delivery = build_client_access_delivery(access_token=access_token, raw_token=raw_token)
    record_audit_event(
        action=AuditLog.Action.CLIENT_ACCESS_LINK_SENT,
        partner_group=access_token.partner_group,
        actor=created_by,
        target=access_token,
        metadata={
            **_audit_metadata(access_token),
            "mock_delivery": True,
            "delivery_channel": access_token.delivery_channel,
        },
    )
    return raw_token, access_token, delivery


def authenticate_client_access_request(request):
    raw_token = extract_raw_token(request)
    if not raw_token:
        raise exceptions.AuthenticationFailed("Jeton client obligatoire.")

    access_token = (
        ClientAccessToken.objects.select_related(
            "partner_group",
            "client",
            "contract",
            "contract__quote",
            "contract__vehicle",
        )
        .filter(token_hash=hash_client_access_token(raw_token))
        .first()
    )
    if access_token is None or not access_token.is_active:
        raise exceptions.AuthenticationFailed("Jeton client invalide ou expire.")

    access_token.used_at = timezone.now()
    access_token.save(update_fields=["used_at"])
    record_audit_event(
        action=AuditLog.Action.CLIENT_ACCESS_TOKEN_USED,
        partner_group=access_token.partner_group,
        actor=None,
        target=access_token,
        metadata=_audit_metadata(access_token),
    )
    return access_token


@transaction.atomic
def revoke_client_access_token(*, access_token, actor=None):
    access_token = ClientAccessToken.objects.select_for_update().get(pk=access_token.pk)
    if access_token.revoked_at is None:
        access_token.revoked_at = timezone.now()
        access_token.save(update_fields=["revoked_at"])
        record_audit_event(
            action=AuditLog.Action.CLIENT_ACCESS_TOKEN_REVOKED,
            partner_group=access_token.partner_group,
            actor=actor,
            target=access_token,
            metadata=_audit_metadata(access_token),
        )
    return access_token


@transaction.atomic
def rotate_client_access_token(*, access_token, actor=None, expires_in_days=None):
    access_token = ClientAccessToken.objects.select_for_update().get(pk=access_token.pk)
    if access_token.revoked_at is None:
        access_token.revoked_at = timezone.now()
        access_token.save(update_fields=["revoked_at"])

    raw_token, rotated_token, delivery = create_client_access_token(
        client=access_token.client,
        contract=access_token.contract,
        created_by=actor,
        delivery_channel=access_token.delivery_channel,
        expires_in_days=expires_in_days,
        rotated_from=access_token,
    )
    record_audit_event(
        action=AuditLog.Action.CLIENT_ACCESS_TOKEN_ROTATED,
        partner_group=rotated_token.partner_group,
        actor=actor,
        target=rotated_token,
        metadata={
            **_audit_metadata(rotated_token),
            "rotated_from_id": access_token.id,
        },
    )
    return raw_token, rotated_token, delivery


def resend_client_access_link(*, access_token, actor=None):
    return rotate_client_access_token(access_token=access_token, actor=actor)


@transaction.atomic
def create_client_access_otp(*, access_token, purpose, delivery_channel=None):
    access_token = (
        ClientAccessToken.objects.select_for_update()
        .select_related("partner_group", "client", "contract")
        .get(pk=access_token.pk)
    )
    if not access_token.is_active:
        raise exceptions.AuthenticationFailed("Jeton client invalide ou expire.")

    delivery_channel = delivery_channel or access_token.delivery_channel
    now = timezone.now()
    _revoke_active_otps(
        access_token=access_token,
        purpose=purpose,
        revoked_at=now,
    )

    raw_otp = generate_raw_client_access_otp()
    otp = ClientAccessOtp(
        partner_group=access_token.partner_group,
        client=access_token.client,
        contract=access_token.contract,
        access_token=access_token,
        otp_hash=hash_client_access_otp(raw_otp, access_token=access_token),
        purpose=purpose,
        delivery_channel=delivery_channel,
        expires_at=now + timedelta(minutes=settings.CLIENT_ACCESS_OTP_TTL_MINUTES),
        sent_at=now,
    )
    otp.full_clean()
    otp.save()
    record_audit_event(
        action=AuditLog.Action.CLIENT_ACCESS_OTP_CREATED,
        partner_group=otp.partner_group,
        actor=None,
        target=otp,
        metadata=_otp_audit_metadata(otp),
    )
    delivery = build_client_otp_delivery(otp=otp)
    record_audit_event(
        action=AuditLog.Action.CLIENT_ACCESS_OTP_SENT,
        partner_group=otp.partner_group,
        actor=None,
        target=otp,
        metadata={
            **_otp_audit_metadata(otp),
            "mock_delivery": True,
            "delivery_channel": otp.delivery_channel,
        },
    )
    return raw_otp, otp, delivery


def verify_client_access_otp(*, access_token, purpose, raw_otp):
    failure = None
    with transaction.atomic():
        access_token = (
            ClientAccessToken.objects.select_for_update()
            .select_related("partner_group", "client", "contract")
            .get(pk=access_token.pk)
        )
        if not access_token.is_active:
            failure = ("auth", "Jeton client invalide ou expire.")
        elif not raw_otp:
            _register_failed_otp_attempt(
                access_token=access_token,
                purpose=purpose,
                reason="missing_otp",
            )
            failure = ("permission", "OTP obligatoire.")
        else:
            otp = (
                ClientAccessOtp.objects.select_for_update()
                .select_related("partner_group", "client", "contract", "access_token")
                .filter(
                    access_token=access_token,
                    purpose=purpose,
                    otp_hash=hash_client_access_otp(raw_otp, access_token=access_token),
                )
                .order_by("-created_at", "-id")
                .first()
            )
            if otp is None or not otp.is_active:
                _register_failed_otp_attempt(
                    access_token=access_token,
                    purpose=purpose,
                    otp=otp,
                    reason="invalid_or_expired_otp",
                )
                failure = ("permission", "OTP invalide ou expire.")
            else:
                otp.used_at = timezone.now()
                otp.save(update_fields=["used_at"])
                record_audit_event(
                    action=AuditLog.Action.CLIENT_ACCESS_OTP_VERIFIED,
                    partner_group=otp.partner_group,
                    actor=None,
                    target=otp,
                    metadata=_otp_audit_metadata(otp),
                )
                return otp

    if failure and failure[0] == "auth":
        raise exceptions.AuthenticationFailed(failure[1])
    raise exceptions.PermissionDenied(
        failure[1] if failure else "OTP invalide ou expire."
    )


def generate_raw_client_access_token():
    return f"{TOKEN_PREFIX}{secrets.token_urlsafe(32)}"


def generate_raw_client_access_otp():
    length = max(4, min(settings.CLIENT_ACCESS_OTP_LENGTH, 12))
    return str(secrets.randbelow(10**length)).zfill(length)


def hash_client_access_token(raw_token):
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def hash_client_access_otp(raw_otp, *, access_token):
    payload = f"{access_token.pk}:{raw_otp}".encode("utf-8")
    return hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()


def extract_raw_token(request):
    authorization = request.headers.get("Authorization", "")
    scheme, _, value = authorization.partition(" ")
    if scheme.lower() == "client-token" and value:
        return value.strip()
    return ""


def extract_raw_otp(request):
    return request.headers.get(OTP_HEADER, "").strip()


def build_client_access_delivery(*, access_token, raw_token):
    access_url = build_client_access_url(raw_token=raw_token, contract_id=access_token.contract_id)
    return {
        "mock_delivery": True,
        "delivery_channel": access_token.delivery_channel,
        "destination": _delivery_destination(access_token),
        "access_url": access_url,
    }


def build_client_access_url(*, raw_token, contract_id):
    base_url = settings.CLIENT_PORTAL_BASE_URL.rstrip("/")
    query = urlencode({"token": raw_token, "contract": contract_id})
    return f"{base_url}/client-space/access?{query}"


def build_client_otp_delivery(*, otp):
    return {
        "mock_delivery": True,
        "delivery_channel": otp.delivery_channel,
        "destination": _delivery_destination(otp),
    }


def _delivery_destination(access_token):
    if access_token.delivery_channel == ClientAccessToken.DeliveryChannel.EMAIL:
        return access_token.client.email
    if access_token.delivery_channel == ClientAccessToken.DeliveryChannel.SMS:
        return access_token.client.phone
    return ""


def _audit_metadata(access_token):
    return {
        "client_id": access_token.client_id,
        "contract_id": access_token.contract_id,
        "partner_group_id": access_token.partner_group_id,
        "delivery_channel": access_token.delivery_channel,
        "expires_at": access_token.expires_at.isoformat(),
    }


def _revoke_active_otps(*, access_token, purpose, revoked_at):
    active_otps = ClientAccessOtp.objects.select_for_update().filter(
        access_token=access_token,
        purpose=purpose,
        used_at__isnull=True,
        revoked_at__isnull=True,
        expires_at__gt=revoked_at,
    )
    for otp in active_otps:
        otp.revoked_at = revoked_at
        otp.save(update_fields=["revoked_at"])
        record_audit_event(
            action=AuditLog.Action.CLIENT_ACCESS_OTP_REVOKED,
            partner_group=otp.partner_group,
            actor=None,
            target=otp,
            metadata={
                **_otp_audit_metadata(otp),
                "reason": "rotated",
            },
        )


def _register_failed_otp_attempt(*, access_token, purpose, reason, otp=None):
    if otp is None:
        otp = (
            ClientAccessOtp.objects.select_for_update()
            .filter(
                access_token=access_token,
                purpose=purpose,
                used_at__isnull=True,
                revoked_at__isnull=True,
                expires_at__gt=timezone.now(),
            )
            .order_by("-created_at", "-id")
            .first()
        )

    if otp is not None and otp.is_active:
        otp.failed_attempts += 1
        update_fields = ["failed_attempts"]
        if otp.failed_attempts >= settings.CLIENT_ACCESS_OTP_MAX_ATTEMPTS:
            otp.revoked_at = timezone.now()
            update_fields.append("revoked_at")
        otp.save(update_fields=update_fields)

    record_audit_event(
        action=AuditLog.Action.CLIENT_ACCESS_OTP_FAILED,
        partner_group=access_token.partner_group,
        actor=None,
        target=otp or access_token,
        metadata={
            "client_id": access_token.client_id,
            "contract_id": access_token.contract_id,
            "partner_group_id": access_token.partner_group_id,
            "purpose": purpose,
            "reason": reason,
        },
    )
    if otp is not None and otp.revoked_at is not None:
        record_audit_event(
            action=AuditLog.Action.CLIENT_ACCESS_OTP_REVOKED,
            partner_group=otp.partner_group,
            actor=None,
            target=otp,
            metadata={
                **_otp_audit_metadata(otp),
                "reason": "max_attempts",
            },
        )


def _otp_audit_metadata(otp):
    return {
        "client_id": otp.client_id,
        "contract_id": otp.contract_id,
        "partner_group_id": otp.partner_group_id,
        "access_token_id": otp.access_token_id,
        "purpose": otp.purpose,
        "delivery_channel": otp.delivery_channel,
        "expires_at": otp.expires_at.isoformat(),
    }
