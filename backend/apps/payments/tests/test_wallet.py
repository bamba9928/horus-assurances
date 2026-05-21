from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.groups.models import PartnerGroup
from apps.payments.models import WalletTransaction
from apps.payments.services import get_or_create_wallet

User = get_user_model()


@pytest.fixture
def wallet_context():
    group_a = PartnerGroup.objects.create(name="Wallet Groupe A", slug="wallet-a")
    group_b = PartnerGroup.objects.create(name="Wallet Groupe B", slug="wallet-b")
    general_admin = User.objects.create_user(
        username="wallet-general",
        password="password",
        role=User.Role.GENERAL_ADMIN,
    )
    group_admin_a = User.objects.create_user(
        username="wallet-admin-a",
        password="password",
        role=User.Role.GROUP_ADMIN,
        partner_group=group_a,
    )
    contributor_a = User.objects.create_user(
        username="wallet-apporteur-a",
        password="password",
        role=User.Role.CONTRIBUTOR,
        partner_group=group_a,
    )
    wallet_a = get_or_create_wallet(group_a)
    wallet_b = get_or_create_wallet(group_b)
    return {
        "group_a": group_a,
        "group_b": group_b,
        "general_admin": general_admin,
        "group_admin_a": group_admin_a,
        "contributor_a": contributor_a,
        "wallet_a": wallet_a,
        "wallet_b": wallet_b,
    }


@pytest.mark.django_db
def test_general_admin_can_list_all_wallets(wallet_context):
    client = APIClient()
    client.force_authenticate(wallet_context["general_admin"])

    response = client.get("/api/v1/wallets/")

    assert response.status_code == status.HTTP_200_OK
    assert {item["partner_group"] for item in response.data} == {
        wallet_context["group_a"].id,
        wallet_context["group_b"].id,
    }


@pytest.mark.django_db
def test_group_admin_can_only_list_own_wallet(wallet_context):
    client = APIClient()
    client.force_authenticate(wallet_context["group_admin_a"])

    response = client.get("/api/v1/wallets/")

    assert response.status_code == status.HTTP_200_OK
    assert [item["partner_group"] for item in response.data] == [
        wallet_context["group_a"].id
    ]


@pytest.mark.django_db
def test_group_admin_cannot_retrieve_wallet_from_another_group(wallet_context):
    client = APIClient()
    client.force_authenticate(wallet_context["group_admin_a"])

    response = client.get(f"/api/v1/wallets/{wallet_context['wallet_b'].id}/")

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_contributor_cannot_list_wallets(wallet_context):
    client = APIClient()
    client.force_authenticate(wallet_context["contributor_a"])

    response = client.get("/api/v1/wallets/")

    assert response.status_code == status.HTTP_200_OK
    assert response.data == []


@pytest.mark.django_db
def test_credit_wallet_is_idempotent(wallet_context):
    client = APIClient()
    client.force_authenticate(wallet_context["group_admin_a"])

    payload = {
        "amount": "50000.00",
        "idempotency_key": "credit-wallet-a-001",
        "reference": "topup-001",
    }
    first_response = client.post(
        f"/api/v1/wallets/{wallet_context['wallet_a'].id}/credit/",
        payload,
        format="json",
    )
    second_response = client.post(
        f"/api/v1/wallets/{wallet_context['wallet_a'].id}/credit/",
        payload,
        format="json",
    )

    wallet_context["wallet_a"].refresh_from_db()
    assert first_response.status_code == status.HTTP_200_OK
    assert second_response.status_code == status.HTTP_200_OK
    assert wallet_context["wallet_a"].balance == Decimal("50000.00")
    assert WalletTransaction.objects.filter(
        partner_group=wallet_context["group_a"],
        idempotency_key="credit-wallet-a-001",
    ).count() == 1


@pytest.mark.django_db
def test_debit_wallet_is_rejected_when_balance_is_insufficient(wallet_context):
    client = APIClient()
    client.force_authenticate(wallet_context["group_admin_a"])

    response = client.post(
        f"/api/v1/wallets/{wallet_context['wallet_a'].id}/debit/",
        {"amount": "1000.00", "idempotency_key": "debit-insufficient-001"},
        format="json",
    )

    wallet_context["wallet_a"].refresh_from_db()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert wallet_context["wallet_a"].balance == Decimal("0.00")


@pytest.mark.django_db
def test_wallet_balance_after_credit_and_debit(wallet_context):
    client = APIClient()
    client.force_authenticate(wallet_context["group_admin_a"])

    credit_response = client.post(
        f"/api/v1/wallets/{wallet_context['wallet_a'].id}/credit/",
        {"amount": "10000.00", "idempotency_key": "credit-balance-001"},
        format="json",
    )
    debit_response = client.post(
        f"/api/v1/wallets/{wallet_context['wallet_a'].id}/debit/",
        {"amount": "2500.00", "idempotency_key": "debit-balance-001"},
        format="json",
    )

    wallet_context["wallet_a"].refresh_from_db()
    assert credit_response.status_code == status.HTTP_200_OK
    assert debit_response.status_code == status.HTTP_200_OK
    assert wallet_context["wallet_a"].balance == Decimal("7500.00")


@pytest.mark.django_db
def test_group_admin_can_only_list_own_wallet_transactions(wallet_context):
    client = APIClient()
    client.force_authenticate(wallet_context["general_admin"])
    client.post(
        f"/api/v1/wallets/{wallet_context['wallet_a'].id}/credit/",
        {"amount": "1000.00", "idempotency_key": "tx-a-001"},
        format="json",
    )
    client.post(
        f"/api/v1/wallets/{wallet_context['wallet_b'].id}/credit/",
        {"amount": "2000.00", "idempotency_key": "tx-b-001"},
        format="json",
    )

    client.force_authenticate(wallet_context["group_admin_a"])
    response = client.get("/api/v1/wallet-transactions/")

    assert response.status_code == status.HTTP_200_OK
    assert [item["partner_group"] for item in response.data] == [
        wallet_context["group_a"].id
    ]
