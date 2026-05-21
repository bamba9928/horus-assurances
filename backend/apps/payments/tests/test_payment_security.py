from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.clients.models import Client
from apps.groups.models import PartnerGroup
from apps.payments.models import Payment, WalletTransaction
from apps.payments.services import get_or_create_wallet
from apps.quotes.models import Quote
from apps.vehicles.models import Vehicle

User = get_user_model()


@pytest.fixture
def payment_context():
    group_a = PartnerGroup.objects.create(name="Payment Groupe A", slug="payment-a")
    group_b = PartnerGroup.objects.create(name="Payment Groupe B", slug="payment-b")
    general_admin = User.objects.create_user(
        username="payment-general",
        password="password",
        role=User.Role.GENERAL_ADMIN,
    )
    group_admin_a = User.objects.create_user(
        username="payment-admin-a",
        password="password",
        role=User.Role.GROUP_ADMIN,
        partner_group=group_a,
    )
    contributor_a = User.objects.create_user(
        username="payment-apporteur-a",
        password="password",
        role=User.Role.CONTRIBUTOR,
        partner_group=group_a,
    )
    contributor_a2 = User.objects.create_user(
        username="payment-apporteur-a2",
        password="password",
        role=User.Role.CONTRIBUTOR,
        partner_group=group_a,
    )
    contributor_b = User.objects.create_user(
        username="payment-apporteur-b",
        password="password",
        role=User.Role.CONTRIBUTOR,
        partner_group=group_b,
    )

    client_a = Client.objects.create(
        partner_group=group_a,
        contributor=contributor_a,
        created_by=contributor_a,
        first_name="Payment",
        last_name="Client A",
        phone="760000001",
    )
    client_a2 = Client.objects.create(
        partner_group=group_a,
        contributor=contributor_a2,
        created_by=contributor_a2,
        first_name="Payment",
        last_name="Client A2",
        phone="760000002",
    )
    client_b = Client.objects.create(
        partner_group=group_b,
        contributor=contributor_b,
        created_by=contributor_b,
        first_name="Payment",
        last_name="Client B",
        phone="760000003",
    )

    vehicle_a = Vehicle.objects.create(
        partner_group=group_a,
        client=client_a,
        contributor=contributor_a,
        created_by=contributor_a,
        registration_number="DK-P01-AA",
        brand="Toyota",
        model="Yaris",
        genre="VP",
        energy=Vehicle.Energy.GASOLINE,
    )
    vehicle_a2 = Vehicle.objects.create(
        partner_group=group_a,
        client=client_a2,
        contributor=contributor_a2,
        created_by=contributor_a2,
        registration_number="DK-P02-AA",
        brand="Hyundai",
        model="i10",
        genre="VP",
        energy=Vehicle.Energy.GASOLINE,
    )
    vehicle_b = Vehicle.objects.create(
        partner_group=group_b,
        client=client_b,
        contributor=contributor_b,
        created_by=contributor_b,
        registration_number="DK-P03-BB",
        brand="Kia",
        model="Rio",
        genre="VP",
        energy=Vehicle.Energy.DIESEL,
    )

    quote_a = Quote.objects.create(
        partner_group=group_a,
        client=client_a,
        vehicle=vehicle_a,
        contributor=contributor_a,
        created_by=contributor_a,
        premium_amount=Decimal("10000.00"),
        fees_amount=Decimal("1000.00"),
        total_amount=Decimal("11000.00"),
    )
    quote_a2 = Quote.objects.create(
        partner_group=group_a,
        client=client_a2,
        vehicle=vehicle_a2,
        contributor=contributor_a2,
        created_by=contributor_a2,
        premium_amount=Decimal("20000.00"),
        fees_amount=Decimal("1000.00"),
        total_amount=Decimal("21000.00"),
    )
    quote_b = Quote.objects.create(
        partner_group=group_b,
        client=client_b,
        vehicle=vehicle_b,
        contributor=contributor_b,
        created_by=contributor_b,
        premium_amount=Decimal("30000.00"),
        fees_amount=Decimal("1000.00"),
        total_amount=Decimal("31000.00"),
    )

    payment_a = Payment.objects.create(
        partner_group=group_a,
        quote=quote_a,
        client=client_a,
        contributor=contributor_a,
        created_by=contributor_a,
        method=Payment.Method.WAVE,
        amount=quote_a.total_amount,
    )
    payment_a2 = Payment.objects.create(
        partner_group=group_a,
        quote=quote_a2,
        client=client_a2,
        contributor=contributor_a2,
        created_by=contributor_a2,
        method=Payment.Method.WAVE,
        amount=quote_a2.total_amount,
    )
    payment_b = Payment.objects.create(
        partner_group=group_b,
        quote=quote_b,
        client=client_b,
        contributor=contributor_b,
        created_by=contributor_b,
        method=Payment.Method.WAVE,
        amount=quote_b.total_amount,
    )

    wallet_a = get_or_create_wallet(group_a)
    wallet_b = get_or_create_wallet(group_b)

    return {
        "group_a": group_a,
        "group_b": group_b,
        "general_admin": general_admin,
        "group_admin_a": group_admin_a,
        "contributor_a": contributor_a,
        "contributor_a2": contributor_a2,
        "contributor_b": contributor_b,
        "client_a": client_a,
        "client_a2": client_a2,
        "client_b": client_b,
        "quote_a": quote_a,
        "quote_a2": quote_a2,
        "quote_b": quote_b,
        "payment_a": payment_a,
        "payment_a2": payment_a2,
        "payment_b": payment_b,
        "wallet_a": wallet_a,
        "wallet_b": wallet_b,
    }


@pytest.mark.django_db
def test_general_admin_can_list_all_payments(payment_context):
    client = APIClient()
    client.force_authenticate(payment_context["general_admin"])

    response = client.get("/api/v1/payments/")

    assert response.status_code == status.HTTP_200_OK
    assert {item["id"] for item in response.data} == {
        payment_context["payment_a"].id,
        payment_context["payment_a2"].id,
        payment_context["payment_b"].id,
    }


@pytest.mark.django_db
def test_group_admin_can_only_list_payments_from_own_group(payment_context):
    client = APIClient()
    client.force_authenticate(payment_context["group_admin_a"])

    response = client.get("/api/v1/payments/")

    assert response.status_code == status.HTTP_200_OK
    assert {item["id"] for item in response.data} == {
        payment_context["payment_a"].id,
        payment_context["payment_a2"].id,
    }


@pytest.mark.django_db
def test_contributor_can_only_list_own_payments(payment_context):
    client = APIClient()
    client.force_authenticate(payment_context["contributor_a"])

    response = client.get("/api/v1/payments/")

    assert response.status_code == status.HTTP_200_OK
    assert [item["id"] for item in response.data] == [payment_context["payment_a"].id]


@pytest.mark.django_db
def test_group_admin_cannot_retrieve_payment_from_another_group(payment_context):
    client = APIClient()
    client.force_authenticate(payment_context["group_admin_a"])

    response = client.get(f"/api/v1/payments/{payment_context['payment_b'].id}/")

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_contributor_cannot_create_payment_for_another_group(payment_context):
    client = APIClient()
    client.force_authenticate(payment_context["contributor_a"])

    response = client.post(
        "/api/v1/payments/",
        {
            "quote": payment_context["quote_b"].id,
            "method": Payment.Method.WAVE,
        },
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_contributor_cannot_create_payment_for_another_contributors_quote(
    payment_context,
):
    client = APIClient()
    client.force_authenticate(payment_context["contributor_a"])

    response = client.post(
        "/api/v1/payments/",
        {
            "quote": payment_context["quote_a2"].id,
            "method": Payment.Method.WAVE,
        },
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_create_payment_infers_group_client_contributor_and_amount(payment_context):
    client = APIClient()
    client.force_authenticate(payment_context["contributor_a"])

    response = client.post(
        "/api/v1/payments/",
        {
            "quote": payment_context["quote_a"].id,
            "method": Payment.Method.WAVE,
            "idempotency_key": "payment-create-001",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED
    created = Payment.objects.get(id=response.data["id"])
    assert created.partner_group == payment_context["group_a"]
    assert created.client == payment_context["client_a"]
    assert created.contributor == payment_context["contributor_a"]
    assert created.amount == Decimal("11000.00")


@pytest.mark.django_db
def test_confirm_wave_payment_is_idempotent(payment_context):
    client = APIClient()
    client.force_authenticate(payment_context["contributor_a"])

    first_response = client.post(
        f"/api/v1/payments/{payment_context['payment_a'].id}/confirm/",
        {"idempotency_key": "confirm-wave-001"},
        format="json",
    )
    second_response = client.post(
        f"/api/v1/payments/{payment_context['payment_a'].id}/confirm/",
        {"idempotency_key": "confirm-wave-001"},
        format="json",
    )

    payment_context["payment_a"].refresh_from_db()
    assert first_response.status_code == status.HTTP_200_OK
    assert second_response.status_code == status.HTTP_200_OK
    assert payment_context["payment_a"].status == Payment.Status.CONFIRMED
    assert payment_context["payment_a"].wallet_transaction is None


@pytest.mark.django_db
def test_confirm_wallet_payment_debits_wallet_once(payment_context):
    client = APIClient()
    client.force_authenticate(payment_context["group_admin_a"])

    credit_response = client.post(
        f"/api/v1/wallets/{payment_context['wallet_a'].id}/credit/",
        {"amount": "50000.00", "idempotency_key": "wallet-payment-credit-001"},
        format="json",
    )
    payment_response = client.post(
        "/api/v1/payments/",
        {
            "quote": payment_context["quote_a"].id,
            "method": Payment.Method.WALLET,
            "idempotency_key": "wallet-payment-create-001",
        },
        format="json",
    )
    payment_id = payment_response.data["id"]

    first_confirm = client.post(
        f"/api/v1/payments/{payment_id}/confirm/",
        {"idempotency_key": "wallet-payment-confirm-001"},
        format="json",
    )
    second_confirm = client.post(
        f"/api/v1/payments/{payment_id}/confirm/",
        {"idempotency_key": "wallet-payment-confirm-001"},
        format="json",
    )

    payment_context["wallet_a"].refresh_from_db()
    payment = Payment.objects.get(id=payment_id)
    assert credit_response.status_code == status.HTTP_200_OK
    assert payment_response.status_code == status.HTTP_201_CREATED
    assert first_confirm.status_code == status.HTTP_200_OK
    assert second_confirm.status_code == status.HTTP_200_OK
    assert payment.status == Payment.Status.CONFIRMED
    assert payment_context["wallet_a"].balance == Decimal("39000.00")
    assert WalletTransaction.objects.filter(
        partner_group=payment_context["group_a"],
        transaction_type=WalletTransaction.TransactionType.PAYMENT,
    ).count() == 1


@pytest.mark.django_db
def test_confirm_wallet_payment_is_rejected_when_balance_is_insufficient(
    payment_context,
):
    client = APIClient()
    client.force_authenticate(payment_context["group_admin_a"])

    payment_response = client.post(
        "/api/v1/payments/",
        {
            "quote": payment_context["quote_a"].id,
            "method": Payment.Method.WALLET,
            "idempotency_key": "wallet-payment-create-002",
        },
        format="json",
    )
    payment_id = payment_response.data["id"]
    confirm_response = client.post(
        f"/api/v1/payments/{payment_id}/confirm/",
        {"idempotency_key": "wallet-payment-confirm-002"},
        format="json",
    )

    payment = Payment.objects.get(id=payment_id)
    payment_context["wallet_a"].refresh_from_db()
    assert payment_response.status_code == status.HTTP_201_CREATED
    assert confirm_response.status_code == status.HTTP_400_BAD_REQUEST
    assert payment.status == Payment.Status.PENDING
    assert payment_context["wallet_a"].balance == Decimal("0.00")
