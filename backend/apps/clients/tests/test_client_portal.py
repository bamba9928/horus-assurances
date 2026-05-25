from decimal import Decimal
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.audit.models import AuditLog
from apps.clients.models import Client, ClientAccessOtp, ClientAccessToken
from apps.contracts.models import Contract
from apps.groups.models import PartnerGroup
from apps.notifications.models import Notification
from apps.notifications.services import create_client_notification
from apps.payments.models import Payment
from apps.quotes.models import Quote
from apps.vehicles.models import Vehicle

User = get_user_model()


@pytest.fixture
def client_portal_context():
    group = PartnerGroup.objects.create(name="Client Portal", slug="client-portal")
    other_group = PartnerGroup.objects.create(
        name="Client Portal Other",
        slug="client-portal-other",
    )
    general_admin = User.objects.create_user(
        username="client-portal-general",
        password="password",
        role=User.Role.GENERAL_ADMIN,
    )
    group_admin = User.objects.create_user(
        username="client-portal-admin",
        password="password",
        role=User.Role.GROUP_ADMIN,
        partner_group=group,
    )
    contributor = User.objects.create_user(
        username="client-portal-apporteur",
        password="password",
        role=User.Role.CONTRIBUTOR,
        partner_group=group,
    )
    other_contributor = User.objects.create_user(
        username="client-portal-other",
        password="password",
        role=User.Role.CONTRIBUTOR,
        partner_group=group,
    )
    cross_group_contributor = User.objects.create_user(
        username="client-portal-cross-group",
        password="password",
        role=User.Role.CONTRIBUTOR,
        partner_group=other_group,
    )
    client_a = Client.objects.create(
        partner_group=group,
        contributor=contributor,
        created_by=contributor,
        first_name="Awa",
        last_name="Client",
        email="awa.client@example.test",
        phone="771000001",
    )
    client_b = Client.objects.create(
        partner_group=group,
        contributor=other_contributor,
        created_by=other_contributor,
        first_name="Baba",
        last_name="Client",
        phone="771000002",
    )
    client_c = Client.objects.create(
        partner_group=other_group,
        contributor=cross_group_contributor,
        created_by=cross_group_contributor,
        first_name="Coumba",
        last_name="Client",
        phone="771000003",
    )
    contract_a = _create_contract(
        client=client_a,
        contributor=contributor,
        registration_number="DK-CLI-001",
        external_reference="CLIENT-ACCESS-PAY-A",
        contract_number="CLIENT-CONTRACT-A",
    )
    contract_b = _create_contract(
        client=client_b,
        contributor=other_contributor,
        registration_number="DK-CLI-002",
        external_reference="CLIENT-ACCESS-PAY-B",
        contract_number="CLIENT-CONTRACT-B",
    )
    contract_c = _create_contract(
        client=client_c,
        contributor=cross_group_contributor,
        registration_number="DK-CLI-003",
        external_reference="CLIENT-ACCESS-PAY-C",
        contract_number="CLIENT-CONTRACT-C",
    )
    notification_a = create_client_notification(
        client=client_a,
        partner_group=group,
        notification_type=Notification.Type.CONTRACT_ISSUED,
        title="Contrat disponible",
        message="Votre attestation est disponible.",
        target=contract_a,
    )
    notification_b = create_client_notification(
        client=client_b,
        partner_group=group,
        notification_type=Notification.Type.CONTRACT_ISSUED,
        title="Contrat B",
        target=contract_b,
    )
    return {
        "group": group,
        "other_group": other_group,
        "general_admin": general_admin,
        "group_admin": group_admin,
        "contributor": contributor,
        "other_contributor": other_contributor,
        "cross_group_contributor": cross_group_contributor,
        "client_a": client_a,
        "client_b": client_b,
        "client_c": client_c,
        "contract_a": contract_a,
        "contract_b": contract_b,
        "contract_c": contract_c,
        "notification_a": notification_a,
        "notification_b": notification_b,
    }


def _create_contract(*, client, contributor, registration_number, external_reference, contract_number):
    vehicle = Vehicle.objects.create(
        partner_group=client.partner_group,
        client=client,
        contributor=contributor,
        created_by=contributor,
        registration_number=registration_number,
        brand="Toyota",
        model="Yaris",
        genre="VP",
        energy=Vehicle.Energy.GASOLINE,
    )
    quote = Quote.objects.create(
        partner_group=client.partner_group,
        client=client,
        vehicle=vehicle,
        contributor=contributor,
        created_by=contributor,
        premium_amount=Decimal("10000.00"),
        fees_amount=Decimal("1000.00"),
        total_amount=Decimal("11000.00"),
    )
    payment = Payment.objects.create(
        partner_group=client.partner_group,
        quote=quote,
        client=client,
        contributor=contributor,
        created_by=contributor,
        method=Payment.Method.WAVE,
        status=Payment.Status.CONFIRMED,
        amount=quote.total_amount,
        external_reference=external_reference,
    )
    return Contract.objects.create(
        partner_group=client.partner_group,
        quote=quote,
        payment=payment,
        client=client,
        vehicle=vehicle,
        contributor=contributor,
        created_by=contributor,
        status=Contract.Status.ISSUED,
        contract_number=contract_number,
        attestation_reference=f"{contract_number}-ATT",
        attestation_url=f"https://documents.example.test/{contract_number}/attestation.pdf",
        carte_brune_url=f"https://documents.example.test/{contract_number}/carte-brune.pdf",
    )


def _issue_access_token(context, *, contract_key="contract_a", user_key="contributor"):
    client = APIClient()
    client.force_authenticate(context[user_key])
    contract = context[contract_key]
    response = client.post(
        "/api/v1/client-access-tokens/",
        {
            "client": contract.client_id,
            "contract": contract.id,
            "delivery_channel": ClientAccessToken.DeliveryChannel.SMS,
            "expires_in_days": 7,
        },
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED
    return response.data["token"], response.data["access_token"]["id"], response.data


def _portal_client(token):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Client-Token {token}")
    return client


def _request_document_otp(
    context,
    token,
    *,
    contract_key="contract_a",
    document_kind="attestation",
):
    response = _portal_client(token).post(
        f"/api/v1/client-space/contracts/{context[contract_key].id}/documents/otp/",
        {"document_kind": document_kind},
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED
    return response.data["otp"], response.data


@pytest.mark.django_db
def test_contributor_can_create_client_access_token(client_portal_context):
    raw_token, token_id, response_data = _issue_access_token(client_portal_context)

    access_token = ClientAccessToken.objects.get(id=token_id)
    assert raw_token.startswith("hca_")
    assert response_data["mock_delivery"] is True
    assert response_data["access_url"].find(raw_token) > 0
    assert access_token.partner_group == client_portal_context["group"]
    assert access_token.client == client_portal_context["client_a"]
    assert access_token.contract == client_portal_context["contract_a"]
    assert AuditLog.objects.filter(
        action=AuditLog.Action.CLIENT_ACCESS_TOKEN_CREATED,
        target_id=str(access_token.id),
    ).exists()
    assert AuditLog.objects.filter(
        action=AuditLog.Action.CLIENT_ACCESS_LINK_SENT,
        target_id=str(access_token.id),
    ).exists()


@pytest.mark.django_db
def test_token_is_not_stored_in_clear_text(client_portal_context):
    raw_token, token_id, _ = _issue_access_token(client_portal_context)
    access_token = ClientAccessToken.objects.get(id=token_id)

    assert access_token.token_hash != raw_token
    assert raw_token not in access_token.token_hash


@pytest.mark.django_db
def test_contributor_cannot_create_token_for_other_contributors_client(
    client_portal_context,
):
    client = APIClient()
    client.force_authenticate(client_portal_context["contributor"])

    response = client.post(
        "/api/v1/client-access-tokens/",
        {
            "client": client_portal_context["client_b"].id,
            "contract": client_portal_context["contract_b"].id,
            "delivery_channel": ClientAccessToken.DeliveryChannel.EMAIL,
        },
        format="json",
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_group_admin_lists_only_own_group_access_tokens(client_portal_context):
    _, token_a_id, _ = _issue_access_token(client_portal_context)
    _, token_c_id, _ = _issue_access_token(
        client_portal_context,
        contract_key="contract_c",
        user_key="cross_group_contributor",
    )
    client = APIClient()
    client.force_authenticate(client_portal_context["group_admin"])

    response = client.get("/api/v1/client-access-tokens/")

    assert response.status_code == status.HTTP_200_OK
    assert [item["id"] for item in response.data] == [token_a_id]
    assert token_c_id not in [item["id"] for item in response.data]


@pytest.mark.django_db
def test_contributor_cannot_retrieve_other_contributors_access_token(
    client_portal_context,
):
    _, token_b_id, _ = _issue_access_token(
        client_portal_context,
        contract_key="contract_b",
        user_key="other_contributor",
    )
    client = APIClient()
    client.force_authenticate(client_portal_context["contributor"])

    response = client.get(f"/api/v1/client-access-tokens/{token_b_id}/")

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_client_space_document_requires_valid_token(client_portal_context):
    response = APIClient().get(
        f"/api/v1/client-space/contracts/{client_portal_context['contract_a'].id}/documents/"
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_expired_token_is_rejected(client_portal_context):
    raw_token, token_id, _ = _issue_access_token(client_portal_context)
    ClientAccessToken.objects.filter(pk=token_id).update(
        expires_at=timezone.now() - timedelta(minutes=1)
    )

    response = _portal_client(raw_token).get("/api/v1/client-space/me/")

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_revoked_token_is_rejected(client_portal_context):
    raw_token, token_id, _ = _issue_access_token(client_portal_context)
    admin_client = APIClient()
    admin_client.force_authenticate(client_portal_context["contributor"])

    revoke_response = admin_client.post(
        f"/api/v1/client-access-tokens/{token_id}/revoke/",
        {},
        format="json",
    )
    portal_response = _portal_client(raw_token).get("/api/v1/client-space/me/")

    assert revoke_response.status_code == status.HTTP_200_OK
    assert portal_response.status_code == status.HTTP_403_FORBIDDEN
    assert AuditLog.objects.filter(
        action=AuditLog.Action.CLIENT_ACCESS_TOKEN_REVOKED,
        target_id=str(token_id),
    ).exists()


@pytest.mark.django_db
def test_rotation_invalidates_old_token(client_portal_context):
    raw_token, token_id, _ = _issue_access_token(client_portal_context)
    admin_client = APIClient()
    admin_client.force_authenticate(client_portal_context["contributor"])

    rotate_response = admin_client.post(
        f"/api/v1/client-access-tokens/{token_id}/renew/",
        {"expires_in_days": 14},
        format="json",
    )
    old_response = _portal_client(raw_token).get("/api/v1/client-space/me/")
    new_response = _portal_client(rotate_response.data["token"]).get(
        "/api/v1/client-space/me/"
    )

    assert rotate_response.status_code == status.HTTP_200_OK
    assert rotate_response.data["token"] != raw_token
    assert old_response.status_code == status.HTTP_403_FORBIDDEN
    assert new_response.status_code == status.HTTP_200_OK
    assert AuditLog.objects.filter(
        action=AuditLog.Action.CLIENT_ACCESS_TOKEN_ROTATED,
        target_id=str(rotate_response.data["access_token"]["id"]),
    ).exists()


@pytest.mark.django_db
def test_resend_link_rotates_and_returns_mock_delivery(client_portal_context):
    raw_token, token_id, _ = _issue_access_token(client_portal_context)
    admin_client = APIClient()
    admin_client.force_authenticate(client_portal_context["contributor"])

    response = admin_client.post(
        f"/api/v1/client-access-tokens/{token_id}/resend-link/",
        {},
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["mock_delivery"] is True
    assert response.data["token"] != raw_token
    assert response.data["access_url"].find(response.data["token"]) > 0


@pytest.mark.django_db
def test_token_from_another_group_cannot_access_contract(client_portal_context):
    raw_token, _, _ = _issue_access_token(client_portal_context)

    response = _portal_client(raw_token).get(
        f"/api/v1/client-space/contracts/{client_portal_context['contract_c'].id}/documents/"
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_client_portal_lists_only_token_contract(client_portal_context):
    raw_token, _, _ = _issue_access_token(client_portal_context)

    response = _portal_client(raw_token).get("/api/v1/client-space/contracts/")

    assert response.status_code == status.HTTP_200_OK
    assert [item["id"] for item in response.data] == [
        client_portal_context["contract_a"].id
    ]
    assert response.data[0]["attestation_available"] is True
    assert response.data[0]["carte_brune_available"] is True
    assert "attestation_url" not in response.data[0]
    assert "carte_brune_url" not in response.data[0]


@pytest.mark.django_db
def test_client_portal_reads_own_contract_documents(client_portal_context):
    raw_token, _, _ = _issue_access_token(client_portal_context)

    response = _portal_client(raw_token).get(
        f"/api/v1/client-space/contracts/{client_portal_context['contract_a'].id}/documents/"
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["attestation_available"] is True
    assert response.data["carte_brune_available"] is True
    assert response.data["otp_required"] is True
    assert "attestation_url" not in response.data
    assert "carte_brune_url" not in response.data
    assert AuditLog.objects.filter(action=AuditLog.Action.CLIENT_ACCESS_TOKEN_USED).exists()


@pytest.mark.django_db
def test_client_portal_attestation_download_requires_otp(
    client_portal_context,
):
    raw_token, _, _ = _issue_access_token(client_portal_context)

    response = _portal_client(raw_token).get(
        f"/api/v1/client-space/contracts/{client_portal_context['contract_a'].id}/documents/attestation/"
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_client_portal_document_otp_is_mocked_and_not_stored_in_clear_text(
    client_portal_context,
):
    raw_token, _, _ = _issue_access_token(client_portal_context)
    raw_otp, response_data = _request_document_otp(client_portal_context, raw_token)
    otp = ClientAccessOtp.objects.get()

    assert response_data["mock_delivery"] is True
    assert response_data["document_kind"] == "attestation"
    assert raw_otp.isdigit()
    assert otp.otp_hash != raw_otp
    assert raw_otp not in otp.otp_hash
    assert otp.sent_at is not None
    assert AuditLog.objects.filter(
        action=AuditLog.Action.CLIENT_ACCESS_OTP_CREATED,
        target_id=str(otp.id),
    ).exists()
    assert AuditLog.objects.filter(
        action=AuditLog.Action.CLIENT_ACCESS_OTP_SENT,
        target_id=str(otp.id),
    ).exists()


@pytest.mark.django_db
def test_client_portal_attestation_download_redirects_with_valid_otp(
    client_portal_context,
):
    raw_token, _, _ = _issue_access_token(client_portal_context)
    raw_otp, _ = _request_document_otp(client_portal_context, raw_token)

    response = _portal_client(raw_token).get(
        f"/api/v1/client-space/contracts/{client_portal_context['contract_a'].id}/documents/attestation/",
        HTTP_X_CLIENT_OTP=raw_otp,
    )
    otp = ClientAccessOtp.objects.get()

    assert response.status_code == status.HTTP_302_FOUND
    assert response["Location"].endswith("/CLIENT-CONTRACT-A/attestation.pdf")
    assert otp.used_at is not None
    assert AuditLog.objects.filter(
        action=AuditLog.Action.CLIENT_ACCESS_OTP_VERIFIED,
        target_id=str(otp.id),
    ).exists()


@pytest.mark.django_db
def test_client_portal_document_otp_is_single_use(client_portal_context):
    raw_token, _, _ = _issue_access_token(client_portal_context)
    raw_otp, _ = _request_document_otp(client_portal_context, raw_token)
    portal_client = _portal_client(raw_token)
    url = (
        f"/api/v1/client-space/contracts/"
        f"{client_portal_context['contract_a'].id}/documents/attestation/"
    )

    first_response = portal_client.get(url, HTTP_X_CLIENT_OTP=raw_otp)
    second_response = portal_client.get(url, HTTP_X_CLIENT_OTP=raw_otp)

    assert first_response.status_code == status.HTTP_302_FOUND
    assert second_response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_client_portal_expired_document_otp_is_rejected(client_portal_context):
    raw_token, _, _ = _issue_access_token(client_portal_context)
    raw_otp, _ = _request_document_otp(client_portal_context, raw_token)
    ClientAccessOtp.objects.update(expires_at=timezone.now() - timedelta(minutes=1))

    response = _portal_client(raw_token).get(
        f"/api/v1/client-space/contracts/{client_portal_context['contract_a'].id}/documents/attestation/",
        HTTP_X_CLIENT_OTP=raw_otp,
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_client_portal_document_otp_purpose_must_match(client_portal_context):
    raw_token, _, _ = _issue_access_token(client_portal_context)
    raw_otp, _ = _request_document_otp(
        client_portal_context,
        raw_token,
        document_kind="attestation",
    )

    response = _portal_client(raw_token).get(
        f"/api/v1/client-space/contracts/{client_portal_context['contract_a'].id}/documents/carte-brune/",
        HTTP_X_CLIENT_OTP=raw_otp,
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_client_portal_new_document_otp_revokes_previous_one(client_portal_context):
    raw_token, _, _ = _issue_access_token(client_portal_context)
    first_otp, _ = _request_document_otp(client_portal_context, raw_token)
    second_otp, _ = _request_document_otp(client_portal_context, raw_token)
    url = (
        f"/api/v1/client-space/contracts/"
        f"{client_portal_context['contract_a'].id}/documents/attestation/"
    )

    first_response = _portal_client(raw_token).get(url, HTTP_X_CLIENT_OTP=first_otp)
    second_response = _portal_client(raw_token).get(url, HTTP_X_CLIENT_OTP=second_otp)

    assert first_response.status_code == status.HTTP_403_FORBIDDEN
    assert second_response.status_code == status.HTTP_302_FOUND
    assert ClientAccessOtp.objects.filter(revoked_at__isnull=False).exists()


@pytest.mark.django_db
def test_client_portal_document_otp_is_locked_after_failed_attempts(
    client_portal_context,
    settings,
):
    settings.CLIENT_ACCESS_OTP_MAX_ATTEMPTS = 2
    raw_token, _, _ = _issue_access_token(client_portal_context)
    raw_otp, _ = _request_document_otp(client_portal_context, raw_token)
    portal_client = _portal_client(raw_token)
    url = (
        f"/api/v1/client-space/contracts/"
        f"{client_portal_context['contract_a'].id}/documents/attestation/"
    )

    first_failed = portal_client.get(url, HTTP_X_CLIENT_OTP="000000")
    second_failed = portal_client.get(url, HTTP_X_CLIENT_OTP="111111")
    correct_after_lock = portal_client.get(url, HTTP_X_CLIENT_OTP=raw_otp)
    otp = ClientAccessOtp.objects.get()

    assert first_failed.status_code == status.HTTP_403_FORBIDDEN
    assert second_failed.status_code == status.HTTP_403_FORBIDDEN
    assert correct_after_lock.status_code == status.HTTP_403_FORBIDDEN
    assert otp.failed_attempts == 2
    assert otp.revoked_at is not None
    assert AuditLog.objects.filter(
        action=AuditLog.Action.CLIENT_ACCESS_OTP_FAILED,
    ).count() >= 2


@pytest.mark.django_db
def test_client_portal_lists_and_marks_own_notifications(client_portal_context):
    raw_token, _, _ = _issue_access_token(client_portal_context)
    portal_client = _portal_client(raw_token)

    list_response = portal_client.get("/api/v1/client-space/notifications/")
    mark_response = portal_client.post(
        f"/api/v1/client-space/notifications/{client_portal_context['notification_a'].id}/mark-read/",
        {},
        format="json",
    )

    client_portal_context["notification_a"].refresh_from_db()
    client_portal_context["notification_b"].refresh_from_db()
    assert list_response.status_code == status.HTTP_200_OK
    assert [item["id"] for item in list_response.data] == [
        client_portal_context["notification_a"].id
    ]
    assert mark_response.status_code == status.HTTP_200_OK
    assert client_portal_context["notification_a"].read_at is not None
    assert client_portal_context["notification_b"].read_at is None
