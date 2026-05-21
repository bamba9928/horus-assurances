from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.clients.models import Client
from apps.commissions.models import CommissionRule
from apps.contracts.models import Contract
from apps.groups.models import PartnerGroup
from apps.notifications.models import Notification
from apps.payments.models import Payment
from apps.quotes.models import Quote
from apps.vehicles.models import Vehicle

User = get_user_model()


class FakeASSContractIssuer:
    def issue(self, contract):
        return {
            "contractNumber": "NOTIF-CONTRACT-001",
            "attestationReference": "NOTIF-ATT-001",
            "qrCodeReference": "NOTIF-QR-001",
        }


@pytest.fixture
def notification_event_context():
    group = PartnerGroup.objects.create(name="Notifications Events", slug="notif-events")
    group_admin = User.objects.create_user(
        username="notif-events-admin",
        password="password",
        role=User.Role.GROUP_ADMIN,
        partner_group=group,
    )
    contributor = User.objects.create_user(
        username="notif-events-apporteur",
        password="password",
        role=User.Role.CONTRIBUTOR,
        partner_group=group,
    )
    client = Client.objects.create(
        partner_group=group,
        contributor=contributor,
        created_by=contributor,
        first_name="Notification",
        last_name="Client",
        phone="710000001",
    )
    vehicle = Vehicle.objects.create(
        partner_group=group,
        client=client,
        contributor=contributor,
        created_by=contributor,
        registration_number="DK-NOT-001",
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
        idempotency_key="notif-confirmed-payment",
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
    return {
        "group": group,
        "group_admin": group_admin,
        "contributor": contributor,
        "quote": quote,
        "pending_payment": pending_payment,
        "confirmed_payment": confirmed_payment,
        "contract": contract,
    }


@pytest.mark.django_db
def test_confirm_payment_creates_notifications_for_contributor_and_group_admin(
    notification_event_context,
):
    client = APIClient()
    client.force_authenticate(notification_event_context["contributor"])

    response = client.post(
        f"/api/v1/payments/{notification_event_context['pending_payment'].id}/confirm/",
        {"idempotency_key": "notif-payment-confirm-001"},
        format="json",
    )

    notifications = Notification.objects.filter(
        notification_type=Notification.Type.PAYMENT_CONFIRMED
    )
    assert response.status_code == status.HTTP_200_OK
    assert {item.recipient for item in notifications} == {
        notification_event_context["contributor"],
        notification_event_context["group_admin"],
    }


@pytest.mark.django_db
def test_issue_contract_creates_notifications_for_contributor_and_group_admin(
    notification_event_context,
    monkeypatch,
):
    monkeypatch.setattr(
        "apps.contracts.services.ASSContractIssuer",
        FakeASSContractIssuer,
    )
    client = APIClient()
    client.force_authenticate(notification_event_context["contributor"])

    response = client.post(
        f"/api/v1/contracts/{notification_event_context['contract'].id}/issue/",
        {},
        format="json",
    )

    notifications = Notification.objects.filter(
        notification_type=Notification.Type.CONTRACT_ISSUED
    )
    assert response.status_code == status.HTTP_200_OK
    assert {item.recipient for item in notifications} == {
        notification_event_context["contributor"],
        notification_event_context["group_admin"],
    }
    assert notifications.first().metadata["contract_number"] == "NOTIF-CONTRACT-001"


@pytest.mark.django_db
def test_generate_commission_creates_notifications_for_contributor_and_group_admin(
    notification_event_context,
    monkeypatch,
):
    monkeypatch.setattr(
        "apps.contracts.services.ASSContractIssuer",
        FakeASSContractIssuer,
    )
    CommissionRule.objects.create(
        partner_group=notification_event_context["group"],
        percentage_rate=Decimal("10.0000"),
        fixed_amount=Decimal("500.00"),
    )
    client = APIClient()
    client.force_authenticate(notification_event_context["group_admin"])
    client.post(
        f"/api/v1/contracts/{notification_event_context['contract'].id}/issue/",
        {},
        format="json",
    )

    response = client.post(
        "/api/v1/commissions/generate-for-contract/",
        {"contract": notification_event_context["contract"].id},
        format="json",
    )

    notifications = Notification.objects.filter(
        notification_type=Notification.Type.COMMISSION_GENERATED
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert {item.recipient for item in notifications} == {
        notification_event_context["contributor"],
        notification_event_context["group_admin"],
    }
    assert notifications.first().metadata["amount"] == "5500.00"


@pytest.mark.django_db
def test_mark_commission_paid_creates_notification_for_contributor_only(
    notification_event_context,
    monkeypatch,
):
    monkeypatch.setattr(
        "apps.contracts.services.ASSContractIssuer",
        FakeASSContractIssuer,
    )
    client = APIClient()
    client.force_authenticate(notification_event_context["group_admin"])
    client.post(
        f"/api/v1/contracts/{notification_event_context['contract'].id}/issue/",
        {},
        format="json",
    )
    commission_response = client.post(
        "/api/v1/commissions/generate-for-contract/",
        {"contract": notification_event_context["contract"].id},
        format="json",
    )

    response = client.post(
        f"/api/v1/commissions/{commission_response.data['id']}/mark-paid/",
        {},
        format="json",
    )

    notifications = Notification.objects.filter(
        notification_type=Notification.Type.COMMISSION_PAID
    )
    assert response.status_code == status.HTTP_200_OK
    assert [item.recipient for item in notifications] == [
        notification_event_context["contributor"]
    ]
