from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.clients.models import Client
from apps.commissions.models import Commission, CommissionRule
from apps.contracts.models import Contract
from apps.groups.models import PartnerGroup
from apps.payments.models import Payment
from apps.quotes.models import Quote
from apps.vehicles.models import Vehicle

User = get_user_model()


@pytest.fixture
def commission_context():
    group = PartnerGroup.objects.create(name="Commission Groupe A", slug="commission-a")
    group_admin = User.objects.create_user(
        username="commission-admin-a",
        password="password",
        role=User.Role.GROUP_ADMIN,
        partner_group=group,
    )
    contributor = User.objects.create_user(
        username="commission-apporteur-a",
        password="password",
        role=User.Role.CONTRIBUTOR,
        partner_group=group,
    )
    client = Client.objects.create(
        partner_group=group,
        contributor=contributor,
        created_by=contributor,
        first_name="Commission",
        last_name="Client",
        phone="740000001",
    )
    vehicle = Vehicle.objects.create(
        partner_group=group,
        client=client,
        contributor=contributor,
        created_by=contributor,
        registration_number="DK-COM-001",
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
        premium_amount=Decimal("50000.00"),
        fees_amount=Decimal("5000.00"),
        total_amount=Decimal("55000.00"),
    )
    payment = Payment.objects.create(
        partner_group=group,
        quote=quote,
        client=client,
        contributor=contributor,
        created_by=contributor,
        method=Payment.Method.WAVE,
        status=Payment.Status.CONFIRMED,
        amount=Decimal("55000.00"),
    )
    contract = Contract.objects.create(
        partner_group=group,
        quote=quote,
        payment=payment,
        client=client,
        vehicle=vehicle,
        contributor=contributor,
        created_by=contributor,
        status=Contract.Status.ISSUED,
        contract_number="ASS-COM-001",
        attestation_reference="ASS-ATT-COM-001",
        qr_code_reference="ASS-QR-COM-001",
    )
    return {
        "group": group,
        "group_admin": group_admin,
        "contributor": contributor,
        "contract": contract,
        "payment": payment,
    }


@pytest.mark.django_db
def test_generate_commission_uses_percentage_and_fixed_amount(commission_context):
    CommissionRule.objects.create(
        partner_group=commission_context["group"],
        percentage_rate=Decimal("10.0000"),
        fixed_amount=Decimal("750.00"),
    )
    client = APIClient()
    client.force_authenticate(commission_context["group_admin"])

    response = client.post(
        "/api/v1/commissions/generate-for-contract/",
        {"contract": commission_context["contract"].id},
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED
    commission = Commission.objects.get()
    assert commission.base_amount == Decimal("50000.00")
    assert commission.percentage_rate == Decimal("10.0000")
    assert commission.fixed_amount == Decimal("750.00")
    assert commission.amount == Decimal("5750.00")
    assert commission.net_to_pay_amount == Decimal("49250.00")
    assert commission.status == Commission.Status.EARNED


@pytest.mark.django_db
def test_contributor_rule_has_priority_over_group_rule(commission_context):
    CommissionRule.objects.create(
        partner_group=commission_context["group"],
        percentage_rate=Decimal("5.0000"),
        fixed_amount=Decimal("0.00"),
    )
    contributor_rule = CommissionRule.objects.create(
        partner_group=commission_context["group"],
        contributor=commission_context["contributor"],
        percentage_rate=Decimal("12.5000"),
        fixed_amount=Decimal("250.00"),
    )
    client = APIClient()
    client.force_authenticate(commission_context["group_admin"])

    response = client.post(
        "/api/v1/commissions/generate-for-contract/",
        {"contract": commission_context["contract"].id},
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED
    commission = Commission.objects.get()
    assert commission.rule == contributor_rule
    assert commission.percentage_rate == Decimal("12.5000")
    assert commission.fixed_amount == Decimal("250.00")
    assert commission.amount == Decimal("6500.00")
    assert commission.net_to_pay_amount == Decimal("48500.00")


@pytest.mark.django_db
def test_generate_commission_defaults_to_zero_without_active_rule(commission_context):
    client = APIClient()
    client.force_authenticate(commission_context["group_admin"])

    response = client.post(
        "/api/v1/commissions/generate-for-contract/",
        {"contract": commission_context["contract"].id},
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED
    commission = Commission.objects.get()
    assert commission.rule is None
    assert commission.percentage_rate == Decimal("0.0000")
    assert commission.fixed_amount == Decimal("0.00")
    assert commission.amount == Decimal("0.00")
    assert commission.net_to_pay_amount == Decimal("55000.00")


@pytest.mark.django_db
def test_generate_commission_is_idempotent(commission_context):
    CommissionRule.objects.create(
        partner_group=commission_context["group"],
        percentage_rate=Decimal("10.0000"),
        fixed_amount=Decimal("0.00"),
    )
    client = APIClient()
    client.force_authenticate(commission_context["group_admin"])

    first_response = client.post(
        "/api/v1/commissions/generate-for-contract/",
        {"contract": commission_context["contract"].id},
        format="json",
    )
    second_response = client.post(
        "/api/v1/commissions/generate-for-contract/",
        {"contract": commission_context["contract"].id},
        format="json",
    )

    assert first_response.status_code == status.HTTP_201_CREATED
    assert second_response.status_code == status.HTTP_201_CREATED
    assert first_response.data["id"] == second_response.data["id"]
    assert Commission.objects.filter(contract=commission_context["contract"]).count() == 1


@pytest.mark.django_db
def test_generate_commission_requires_issued_contract(commission_context):
    Contract.objects.filter(pk=commission_context["contract"].pk).update(
        status=Contract.Status.READY_TO_ISSUE,
        contract_number=None,
        attestation_reference=None,
        qr_code_reference=None,
    )
    client = APIClient()
    client.force_authenticate(commission_context["group_admin"])

    response = client.post(
        "/api/v1/commissions/generate-for-contract/",
        {"contract": commission_context["contract"].id},
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert Commission.objects.count() == 0


@pytest.mark.django_db
def test_fixed_amount_cannot_exceed_ass_fees(commission_context):
    CommissionRule.objects.create(
        partner_group=commission_context["group"],
        percentage_rate=Decimal("10.0000"),
        fixed_amount=Decimal("5000.01"),
    )
    client = APIClient()
    client.force_authenticate(commission_context["group_admin"])

    response = client.post(
        "/api/v1/commissions/generate-for-contract/",
        {"contract": commission_context["contract"].id},
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert Commission.objects.count() == 0


@pytest.mark.django_db
def test_commission_cannot_exceed_ass_ttc(commission_context):
    CommissionRule.objects.create(
        partner_group=commission_context["group"],
        percentage_rate=Decimal("120.0000"),
        fixed_amount=Decimal("0.00"),
    )
    client = APIClient()
    client.force_authenticate(commission_context["group_admin"])

    response = client.post(
        "/api/v1/commissions/generate-for-contract/",
        {"contract": commission_context["contract"].id},
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert Commission.objects.count() == 0


@pytest.mark.django_db
def test_mark_commission_paid(commission_context):
    client = APIClient()
    client.force_authenticate(commission_context["group_admin"])
    commission_response = client.post(
        "/api/v1/commissions/generate-for-contract/",
        {"contract": commission_context["contract"].id},
        format="json",
    )

    response = client.post(
        f"/api/v1/commissions/{commission_response.data['id']}/mark-paid/",
        {},
        format="json",
    )

    commission = Commission.objects.get()
    assert response.status_code == status.HTTP_200_OK
    assert commission.status == Commission.Status.PAID
    assert commission.paid_at is not None
