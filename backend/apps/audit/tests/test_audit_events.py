from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.audit.models import AuditLog
from apps.clients.models import Client
from apps.commissions.models import CommissionRule
from apps.contracts.models import Contract
from apps.groups.models import PartnerGroup
from apps.payments.models import Payment
from apps.payments.services import get_or_create_wallet
from apps.quotes.models import Quote
from apps.vehicles.models import Vehicle

User = get_user_model()


class FakeASSContractIssuer:
    def issue(self, contract):
        return {
            "contractNumber": "AUDIT-CONTRACT-001",
            "attestationReference": "AUDIT-ATT-001",
            "qrCodeReference": "AUDIT-QR-001",
        }


@pytest.fixture
def audit_event_context():
    group = PartnerGroup.objects.create(name="Audit Events Groupe", slug="audit-events")
    group_admin = User.objects.create_user(
        username="audit-events-admin",
        password="password",
        role=User.Role.GROUP_ADMIN,
        partner_group=group,
    )
    contributor = User.objects.create_user(
        username="audit-events-apporteur",
        password="password",
        role=User.Role.CONTRIBUTOR,
        partner_group=group,
    )
    client = Client.objects.create(
        partner_group=group,
        contributor=contributor,
        created_by=contributor,
        first_name="Audit",
        last_name="Client",
        phone="720000001",
    )
    vehicle = Vehicle.objects.create(
        partner_group=group,
        client=client,
        contributor=contributor,
        created_by=contributor,
        registration_number="DK-AUD-001",
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
    pending_payment = Payment.objects.create(
        partner_group=group,
        quote=quote,
        client=client,
        contributor=contributor,
        created_by=contributor,
        method=Payment.Method.WAVE,
        status=Payment.Status.PENDING,
        amount=quote.total_amount,
    )
    confirmed_payment = Payment.objects.create(
        partner_group=group,
        quote=quote,
        client=client,
        contributor=contributor,
        created_by=contributor,
        method=Payment.Method.WAVE,
        status=Payment.Status.CONFIRMED,
        amount=quote.total_amount,
        idempotency_key="audit-confirmed-payment",
    )
    contract = Contract.objects.create(
        partner_group=group,
        quote=quote,
        payment=confirmed_payment,
        client=client,
        vehicle=vehicle,
        contributor=contributor,
        created_by=contributor,
    )
    wallet = get_or_create_wallet(group)
    return {
        "group": group,
        "group_admin": group_admin,
        "contributor": contributor,
        "quote": quote,
        "pending_payment": pending_payment,
        "confirmed_payment": confirmed_payment,
        "contract": contract,
        "wallet": wallet,
    }


@pytest.mark.django_db
def test_credit_wallet_creates_audit_log(audit_event_context):
    client = APIClient()
    client.force_authenticate(audit_event_context["group_admin"])

    response = client.post(
        f"/api/v1/wallets/{audit_event_context['wallet'].id}/credit/",
        {"amount": "10000.00", "idempotency_key": "audit-credit-001"},
        format="json",
    )

    log = AuditLog.objects.get(action=AuditLog.Action.WALLET_CREDITED)
    assert response.status_code == status.HTTP_200_OK
    assert log.partner_group == audit_event_context["group"]
    assert log.actor == audit_event_context["group_admin"]
    assert log.metadata["amount"] == "10000.00"


@pytest.mark.django_db
def test_debit_wallet_creates_audit_log(audit_event_context):
    client = APIClient()
    client.force_authenticate(audit_event_context["group_admin"])
    client.post(
        f"/api/v1/wallets/{audit_event_context['wallet'].id}/credit/",
        {"amount": "10000.00", "idempotency_key": "audit-debit-credit-001"},
        format="json",
    )

    response = client.post(
        f"/api/v1/wallets/{audit_event_context['wallet'].id}/debit/",
        {"amount": "2500.00", "idempotency_key": "audit-debit-001"},
        format="json",
    )

    log = AuditLog.objects.get(action=AuditLog.Action.WALLET_DEBITED)
    assert response.status_code == status.HTTP_200_OK
    assert log.partner_group == audit_event_context["group"]
    assert log.actor == audit_event_context["group_admin"]
    assert log.metadata["amount"] == "2500.00"


@pytest.mark.django_db
def test_confirm_payment_creates_audit_log(audit_event_context):
    client = APIClient()
    client.force_authenticate(audit_event_context["contributor"])

    response = client.post(
        f"/api/v1/payments/{audit_event_context['pending_payment'].id}/confirm/",
        {"idempotency_key": "audit-confirm-payment-001"},
        format="json",
    )

    log = AuditLog.objects.get(action=AuditLog.Action.PAYMENT_CONFIRMED)
    assert response.status_code == status.HTTP_200_OK
    assert log.partner_group == audit_event_context["group"]
    assert log.actor == audit_event_context["contributor"]
    assert log.metadata["method"] == Payment.Method.WAVE


@pytest.mark.django_db
def test_issue_contract_creates_audit_log(audit_event_context, monkeypatch):
    monkeypatch.setattr(
        "apps.contracts.services.ASSContractIssuer",
        FakeASSContractIssuer,
    )
    client = APIClient()
    client.force_authenticate(audit_event_context["contributor"])

    response = client.post(
        f"/api/v1/contracts/{audit_event_context['contract'].id}/issue/",
        {},
        format="json",
    )

    log = AuditLog.objects.get(action=AuditLog.Action.CONTRACT_ISSUED)
    assert response.status_code == status.HTTP_200_OK
    assert log.partner_group == audit_event_context["group"]
    assert log.actor == audit_event_context["contributor"]
    assert log.metadata["contract_number"] == "AUDIT-CONTRACT-001"


@pytest.mark.django_db
def test_generate_commission_creates_audit_log(audit_event_context, monkeypatch):
    monkeypatch.setattr(
        "apps.contracts.services.ASSContractIssuer",
        FakeASSContractIssuer,
    )
    CommissionRule.objects.create(
        partner_group=audit_event_context["group"],
        percentage_rate=Decimal("10.0000"),
        fixed_amount=Decimal("500.00"),
    )
    client = APIClient()
    client.force_authenticate(audit_event_context["group_admin"])
    client.post(
        f"/api/v1/contracts/{audit_event_context['contract'].id}/issue/",
        {},
        format="json",
    )

    response = client.post(
        "/api/v1/commissions/generate-for-contract/",
        {"contract": audit_event_context["contract"].id},
        format="json",
    )

    log = AuditLog.objects.get(action=AuditLog.Action.COMMISSION_GENERATED)
    assert response.status_code == status.HTTP_201_CREATED
    assert log.partner_group == audit_event_context["group"]
    assert log.actor == audit_event_context["group_admin"]
    assert log.metadata["amount"] == "5500.00"


@pytest.mark.django_db
def test_mark_commission_paid_creates_audit_log(audit_event_context, monkeypatch):
    monkeypatch.setattr(
        "apps.contracts.services.ASSContractIssuer",
        FakeASSContractIssuer,
    )
    client = APIClient()
    client.force_authenticate(audit_event_context["group_admin"])
    client.post(
        f"/api/v1/contracts/{audit_event_context['contract'].id}/issue/",
        {},
        format="json",
    )
    commission_response = client.post(
        "/api/v1/commissions/generate-for-contract/",
        {"contract": audit_event_context["contract"].id},
        format="json",
    )

    response = client.post(
        f"/api/v1/commissions/{commission_response.data['id']}/mark-paid/",
        {},
        format="json",
    )

    log = AuditLog.objects.get(action=AuditLog.Action.COMMISSION_PAID)
    assert response.status_code == status.HTTP_200_OK
    assert log.partner_group == audit_event_context["group"]
    assert log.actor == audit_event_context["group_admin"]
