from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.clients.models import Client
from apps.contracts.models import Contract
from apps.groups.models import PartnerGroup
from apps.payments.models import Payment
from apps.quotes.models import Quote
from apps.vehicles.models import Vehicle

User = get_user_model()


@pytest.fixture
def contract_context():
    group_a = PartnerGroup.objects.create(name="Contract Groupe A", slug="contract-a")
    group_b = PartnerGroup.objects.create(name="Contract Groupe B", slug="contract-b")
    general_admin = User.objects.create_user(
        username="contract-general",
        password="password",
        role=User.Role.GENERAL_ADMIN,
    )
    group_admin_a = User.objects.create_user(
        username="contract-admin-a",
        password="password",
        role=User.Role.GROUP_ADMIN,
        partner_group=group_a,
    )
    contributor_a = User.objects.create_user(
        username="contract-apporteur-a",
        password="password",
        role=User.Role.CONTRIBUTOR,
        partner_group=group_a,
    )
    contributor_a2 = User.objects.create_user(
        username="contract-apporteur-a2",
        password="password",
        role=User.Role.CONTRIBUTOR,
        partner_group=group_a,
    )
    contributor_b = User.objects.create_user(
        username="contract-apporteur-b",
        password="password",
        role=User.Role.CONTRIBUTOR,
        partner_group=group_b,
    )

    client_a = Client.objects.create(
        partner_group=group_a,
        contributor=contributor_a,
        created_by=contributor_a,
        first_name="Contract",
        last_name="Client A",
        phone="750000001",
    )
    client_a2 = Client.objects.create(
        partner_group=group_a,
        contributor=contributor_a2,
        created_by=contributor_a2,
        first_name="Contract",
        last_name="Client A2",
        phone="750000002",
    )
    client_b = Client.objects.create(
        partner_group=group_b,
        contributor=contributor_b,
        created_by=contributor_b,
        first_name="Contract",
        last_name="Client B",
        phone="750000003",
    )

    vehicle_a = Vehicle.objects.create(
        partner_group=group_a,
        client=client_a,
        contributor=contributor_a,
        created_by=contributor_a,
        registration_number="DK-C01-AA",
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
        registration_number="DK-C02-AA",
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
        registration_number="DK-C03-BB",
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

    confirmed_payment_a = Payment.objects.create(
        partner_group=group_a,
        quote=quote_a,
        client=client_a,
        contributor=contributor_a,
        created_by=contributor_a,
        method=Payment.Method.WAVE,
        status=Payment.Status.CONFIRMED,
        amount=quote_a.total_amount,
    )
    confirmed_payment_a2 = Payment.objects.create(
        partner_group=group_a,
        quote=quote_a2,
        client=client_a2,
        contributor=contributor_a2,
        created_by=contributor_a2,
        method=Payment.Method.WAVE,
        status=Payment.Status.CONFIRMED,
        amount=quote_a2.total_amount,
    )
    confirmed_payment_b = Payment.objects.create(
        partner_group=group_b,
        quote=quote_b,
        client=client_b,
        contributor=contributor_b,
        created_by=contributor_b,
        method=Payment.Method.WAVE,
        status=Payment.Status.CONFIRMED,
        amount=quote_b.total_amount,
    )
    pending_payment_a = Payment.objects.create(
        partner_group=group_a,
        quote=quote_a,
        client=client_a,
        contributor=contributor_a,
        created_by=contributor_a,
        method=Payment.Method.WAVE,
        status=Payment.Status.PENDING,
        amount=quote_a.total_amount,
        idempotency_key="pending-contract-a",
    )

    contract_a = Contract.objects.create(
        partner_group=group_a,
        quote=quote_a,
        payment=confirmed_payment_a,
        client=client_a,
        vehicle=vehicle_a,
        contributor=contributor_a,
        created_by=contributor_a,
    )
    contract_b = Contract.objects.create(
        partner_group=group_b,
        quote=quote_b,
        payment=confirmed_payment_b,
        client=client_b,
        vehicle=vehicle_b,
        contributor=contributor_b,
        created_by=contributor_b,
    )

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
        "confirmed_payment_a": confirmed_payment_a,
        "confirmed_payment_a2": confirmed_payment_a2,
        "confirmed_payment_b": confirmed_payment_b,
        "pending_payment_a": pending_payment_a,
        "contract_a": contract_a,
        "contract_b": contract_b,
    }


@pytest.mark.django_db
def test_general_admin_can_list_all_contracts(contract_context):
    client = APIClient()
    client.force_authenticate(contract_context["general_admin"])

    response = client.get("/api/v1/contracts/")

    assert response.status_code == status.HTTP_200_OK
    assert {item["id"] for item in response.data} == {
        contract_context["contract_a"].id,
        contract_context["contract_b"].id,
    }


@pytest.mark.django_db
def test_group_admin_can_only_list_contracts_from_own_group(contract_context):
    client = APIClient()
    client.force_authenticate(contract_context["group_admin_a"])

    response = client.get("/api/v1/contracts/")

    assert response.status_code == status.HTTP_200_OK
    assert [item["id"] for item in response.data] == [contract_context["contract_a"].id]


@pytest.mark.django_db
def test_contributor_can_only_list_own_contracts(contract_context):
    client = APIClient()
    client.force_authenticate(contract_context["contributor_a"])

    response = client.get("/api/v1/contracts/")

    assert response.status_code == status.HTTP_200_OK
    assert [item["id"] for item in response.data] == [contract_context["contract_a"].id]


@pytest.mark.django_db
def test_group_admin_cannot_retrieve_contract_from_another_group(contract_context):
    client = APIClient()
    client.force_authenticate(contract_context["group_admin_a"])

    response = client.get(f"/api/v1/contracts/{contract_context['contract_b'].id}/")

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_contract_cannot_be_created_with_unconfirmed_payment(contract_context):
    client = APIClient()
    client.force_authenticate(contract_context["group_admin_a"])

    response = client.post(
        "/api/v1/contracts/create-from-payment/",
        {"payment": contract_context["pending_payment_a"].id},
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_group_admin_cannot_create_contract_from_other_group_payment(contract_context):
    client = APIClient()
    client.force_authenticate(contract_context["group_admin_a"])

    response = client.post(
        "/api/v1/contracts/create-from-payment/",
        {"payment": contract_context["confirmed_payment_b"].id},
        format="json",
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_contributor_cannot_create_contract_for_another_contributor(
    contract_context,
):
    client = APIClient()
    client.force_authenticate(contract_context["contributor_a"])

    response = client.post(
        "/api/v1/contracts/create-from-payment/",
        {"payment": contract_context["confirmed_payment_a2"].id},
        format="json",
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_create_contract_from_payment_does_not_duplicate_existing_quote(
    contract_context,
):
    client = APIClient()
    client.force_authenticate(contract_context["contributor_a"])

    response = client.post(
        "/api/v1/contracts/create-from-payment/",
        {"payment": contract_context["confirmed_payment_a"].id},
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["id"] == contract_context["contract_a"].id
    assert Contract.objects.filter(quote=contract_context["quote_a"]).count() == 1


@pytest.mark.django_db
def test_direct_contract_create_rejects_duplicate_quote(contract_context):
    client = APIClient()
    client.force_authenticate(contract_context["group_admin_a"])

    response = client.post(
        "/api/v1/contracts/",
        {"payment": contract_context["confirmed_payment_a"].id},
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_issue_contract_is_idempotent(contract_context):
    client = APIClient()
    client.force_authenticate(contract_context["contributor_a"])

    first_response = client.post(
        f"/api/v1/contracts/{contract_context['contract_a'].id}/issue/",
        {},
        format="json",
    )
    second_response = client.post(
        f"/api/v1/contracts/{contract_context['contract_a'].id}/issue/",
        {},
        format="json",
    )

    contract_context["contract_a"].refresh_from_db()
    assert first_response.status_code == status.HTTP_200_OK
    assert second_response.status_code == status.HTTP_200_OK
    assert contract_context["contract_a"].status == Contract.Status.ISSUED
    assert contract_context["contract_a"].contract_number.startswith("HORUS-")
    assert first_response.data["contract_number"] == second_response.data["contract_number"]


@pytest.mark.django_db
def test_issue_contract_rejects_unconfirmed_payment(contract_context):
    Payment.objects.filter(pk=contract_context["confirmed_payment_a"].pk).update(
        status=Payment.Status.PENDING,
        confirmed_at=None,
    )
    client = APIClient()
    client.force_authenticate(contract_context["contributor_a"])

    response = client.post(
        f"/api/v1/contracts/{contract_context['contract_a'].id}/issue/",
        {},
        format="json",
    )

    contract_context["contract_a"].refresh_from_db()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert contract_context["contract_a"].status == Contract.Status.READY_TO_ISSUE
    assert contract_context["contract_a"].contract_number is None
