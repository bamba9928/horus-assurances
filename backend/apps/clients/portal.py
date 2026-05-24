import hashlib
import secrets
from datetime import timedelta
from urllib.parse import urlencode

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework import exceptions

from apps.audit.models import AuditLog
from apps.audit.services import record_audit_event

from .models import ClientAccessToken

TOKEN_PREFIX = "hca_"


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


def generate_raw_client_access_token():
    return f"{TOKEN_PREFIX}{secrets.token_urlsafe(32)}"


def hash_client_access_token(raw_token):
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def extract_raw_token(request):
    authorization = request.headers.get("Authorization", "")
    scheme, _, value = authorization.partition(" ")
    if scheme.lower() == "client-token" and value:
        return value.strip()
    return ""


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
