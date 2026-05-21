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
def commission_security_context():
    group_a = PartnerGroup.objects.create(name="Commission Sec A", slug="commission-sec-a")
    group_b = PartnerGroup.objects.create(name="Commission Sec B", slug="commission-sec-b")
    general_admin = User.objects.create_user(
        username="commission-general",
        password="password",
        role=User.Role.GENERAL_ADMIN,
    )
    group_admin_a = User.objects.create_user(
        username="commission-sec-admin-a",
        password="password",
        role=User.Role.GROUP_ADMIN,
        partner_group=group_a,
    )
    contributor_a = User.objects.create_user(
        username="commission-sec-apporteur-a",
        password="password",
        role=User.Role.CONTRIBUTOR,
        partner_group=group_a,
    )
    contributor_b = User.objects.create_user(
        username="commission-sec-apporteur-b",
        password="password",
        role=User.Role.CONTRIBUTOR,
        partner_group=group_b,
    )

    contract_a = _create_issued_contract(group_a, contributor_a, "A", "730000001")
    contract_b = _create_issued_contract(group_b, contributor_b, "B", "730000002")
    commission_a = Commission.objects.create(
        partner_group=group_a,
        contract=contract_a,
        payment=contract_a.payment,
        contributor=contributor_a,
        base_amount=contract_a.payment.amount,
        percentage_rate=Decimal("10.0000"),
        fixed_amount=Decimal("0.00"),
        amount=Decimal("1100.00"),
        net_to_pay_amount=Decimal("9900.00"),
        status=Commission.Status.EARNED,
    )
    commission_b = Commission.objects.create(
        partner_group=group_b,
        contract=contract_b,
        payment=contract_b.payment,
        contributor=contributor_b,
        base_amount=contract_b.payment.amount,
        percentage_rate=Decimal("10.0000"),
        fixed_amount=Decimal("0.00"),
        amount=Decimal("1100.00"),
        net_to_pay_amount=Decimal("9900.00"),
        status=Commission.Status.EARNED,
    )
    return {
        "group_a": group_a,
        "group_b": group_b,
        "general_admin": general_admin,
        "group_admin_a": group_admin_a,
        "contributor_a": contributor_a,
        "contributor_b": contributor_b,
        "contract_a": contract_a,
        "contract_b": contract_b,
        "commission_a": commission_a,
        "commission_b": commission_b,
    }


def _create_issued_contract(group, contributor, suffix, phone):
    client = Client.objects.create(
        partner_group=group,
        contributor=contributor,
        created_by=contributor,
        first_name="Commission",
        last_name=f"Security {suffix}",
        phone=phone,
    )
    vehicle = Vehicle.objects.create(
        partner_group=group,
        client=client,
        contributor=contributor,
        created_by=contributor,
        registration_number=f"DK-CS-{suffix}",
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
    payment = Payment.objects.create(
        partner_group=group,
        quote=quote,
        client=client,
        contributor=contributor,
        created_by=contributor,
        method=Payment.Method.WAVE,
        status=Payment.Status.CONFIRMED,
        amount=quote.total_amount,
    )
    return Contract.objects.create(
        partner_group=group,
        quote=quote,
        payment=payment,
        client=client,
        vehicle=vehicle,
        contributor=contributor,
        created_by=contributor,
        status=Contract.Status.ISSUED,
        contract_number=f"ASS-CS-{suffix}",
        attestation_reference=f"ASS-ATT-CS-{suffix}",
        qr_code_reference=f"ASS-QR-CS-{suffix}",
    )


@pytest.mark.django_db
def test_general_admin_can_list_all_commissions(commission_security_context):
    client = APIClient()
    client.force_authenticate(commission_security_context["general_admin"])

    response = client.get("/api/v1/commissions/")

    assert response.status_code == status.HTTP_200_OK
    assert {item["id"] for item in response.data} == {
        commission_security_context["commission_a"].id,
        commission_security_context["commission_b"].id,
    }


@pytest.mark.django_db
def test_group_admin_can_only_list_commissions_from_own_group(
    commission_security_context,
):
    client = APIClient()
    client.force_authenticate(commission_security_context["group_admin_a"])

    response = client.get("/api/v1/commissions/")

    assert response.status_code == status.HTTP_200_OK
    assert [item["id"] for item in response.data] == [
        commission_security_context["commission_a"].id
    ]


@pytest.mark.django_db
def test_contributor_can_only_list_own_commissions(commission_security_context):
    client = APIClient()
    client.force_authenticate(commission_security_context["contributor_a"])

    response = client.get("/api/v1/commissions/")

    assert response.status_code == status.HTTP_200_OK
    assert [item["id"] for item in response.data] == [
        commission_security_context["commission_a"].id
    ]


@pytest.mark.django_db
def test_group_admin_cannot_retrieve_other_group_commission(
    commission_security_context,
):
    client = APIClient()
    client.force_authenticate(commission_security_context["group_admin_a"])

    response = client.get(
        f"/api/v1/commissions/{commission_security_context['commission_b'].id}/"
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_group_admin_cannot_create_rule_for_other_group(commission_security_context):
    client = APIClient()
    client.force_authenticate(commission_security_context["group_admin_a"])

    response = client.post(
        "/api/v1/commission-rules/",
        {
            "partner_group": commission_security_context["group_b"].id,
            "percentage_rate": "10.0000",
            "fixed_amount": "0.00",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_contributor_cannot_create_commission_rule(commission_security_context):
    client = APIClient()
    client.force_authenticate(commission_security_context["contributor_a"])

    response = client.post(
        "/api/v1/commission-rules/",
        {
            "percentage_rate": "10.0000",
            "fixed_amount": "0.00",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_group_admin_can_create_and_update_own_group_rule(
    commission_security_context,
):
    client = APIClient()
    client.force_authenticate(commission_security_context["group_admin_a"])

    create_response = client.post(
        "/api/v1/commission-rules/",
        {
            "percentage_rate": "7.5000",
            "fixed_amount": "250.00",
        },
        format="json",
    )
    update_response = client.patch(
        f"/api/v1/commission-rules/{create_response.data['id']}/",
        {"percentage_rate": "8.0000", "fixed_amount": "300.00"},
        format="json",
    )

    rule = CommissionRule.objects.get(id=create_response.data["id"])
    assert create_response.status_code == status.HTTP_201_CREATED
    assert update_response.status_code == status.HTTP_200_OK
    assert rule.partner_group == commission_security_context["group_a"]
    assert rule.percentage_rate == Decimal("8.0000")
    assert rule.fixed_amount == Decimal("300.00")


@pytest.mark.django_db
def test_contributor_cannot_mark_commission_paid(commission_security_context):
    client = APIClient()
    client.force_authenticate(commission_security_context["contributor_a"])

    response = client.post(
        f"/api/v1/commissions/{commission_security_context['commission_a'].id}/mark-paid/",
        {},
        format="json",
    )

    commission_security_context["commission_a"].refresh_from_db()
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert commission_security_context["commission_a"].status == Commission.Status.EARNED


@pytest.mark.django_db
def test_group_admin_cannot_generate_commission_for_other_group_contract(
    commission_security_context,
):
    Commission.objects.all().delete()
    client = APIClient()
    client.force_authenticate(commission_security_context["group_admin_a"])

    response = client.post(
        "/api/v1/commissions/generate-for-contract/",
        {"contract": commission_security_context["contract_b"].id},
        format="json",
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert Commission.objects.count() == 0
