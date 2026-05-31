from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.clients.models import Client
from apps.commissions.models import Commission
from apps.contracts.models import Contract
from apps.groups.models import PartnerGroup
from apps.payments.models import Payment
from apps.quotes.models import Quote
from apps.vehicles.models import Vehicle

User = get_user_model()


@pytest.fixture
def production_context():
    group_a = PartnerGroup.objects.create(name="Production Groupe A", slug="prod-a")
    group_b = PartnerGroup.objects.create(name="Production Groupe B", slug="prod-b")
    general_admin = User.objects.create_user(
        username="production-general",
        password="password",
        role=User.Role.GENERAL_ADMIN,
    )
    group_admin_a = User.objects.create_user(
        username="production-admin-a",
        password="password",
        role=User.Role.GROUP_ADMIN,
        partner_group=group_a,
    )
    contributor_a = User.objects.create_user(
        username="production-apporteur-a",
        password="password",
        role=User.Role.CONTRIBUTOR,
        partner_group=group_a,
    )
    contributor_a2 = User.objects.create_user(
        username="production-apporteur-a2",
        password="password",
        role=User.Role.CONTRIBUTOR,
        partner_group=group_a,
    )
    contributor_b = User.objects.create_user(
        username="production-apporteur-b",
        password="password",
        role=User.Role.CONTRIBUTOR,
        partner_group=group_b,
    )
    client_a = _client(group_a, contributor_a, "Awa", "Prod", "771110001")
    client_a2 = _client(group_a, contributor_a2, "Binta", "Prod", "771110002")
    client_b = _client(group_b, contributor_b, "Cheikh", "Prod", "771110003")

    contract_auto = _contract(
        group=group_a,
        contributor=contributor_a,
        client=client_a,
        product_type=Quote.ProductType.AUTO,
        registration_number="DK-PROD-001",
        contract_status=Contract.Status.ISSUED,
        payment_status=Payment.Status.CONFIRMED,
        amount=Decimal("10000.00"),
        commission_amount=Decimal("1000.00"),
        created_at=_aware(2026, 5, 29),
        contract_number="ASS-AUTO-PROD-001",
        attestation_reference="SNPROD001",
        attestation_url="https://documents.example.test/auto/attestation.pdf",
        carte_brune_url="https://documents.example.test/auto/carte-brune.pdf",
    )
    contract_pending = _contract(
        group=group_a,
        contributor=contributor_a,
        client=client_a,
        product_type=Quote.ProductType.MOTO,
        registration_number="DK-PROD-002",
        contract_status=Contract.Status.READY_TO_ISSUE,
        payment_status=Payment.Status.PENDING,
        amount=Decimal("20000.00"),
        commission_amount=Decimal("0.00"),
        created_at=_aware(2026, 5, 10),
    )
    contract_failed = _contract(
        group=group_a,
        contributor=contributor_a,
        client=client_a,
        product_type=Quote.ProductType.GARAGE,
        registration_number="DK-PROD-003",
        contract_status=Contract.Status.CANCELLED,
        payment_status=Payment.Status.FAILED,
        amount=Decimal("30000.00"),
        commission_amount=Decimal("0.00"),
        created_at=_aware(2026, 4, 20),
    )
    contract_other_contributor = _contract(
        group=group_a,
        contributor=contributor_a2,
        client=client_a2,
        product_type=Quote.ProductType.AUTO,
        registration_number="DK-PROD-004",
        contract_status=Contract.Status.ISSUED,
        payment_status=Payment.Status.CONFIRMED,
        amount=Decimal("40000.00"),
        commission_amount=Decimal("4000.00"),
        created_at=_aware(2026, 5, 15),
        contract_number="ASS-AUTO-PROD-004",
    )
    contract_trailer = _contract(
        group=group_a,
        contributor=contributor_a,
        client=client_a,
        product_type=Quote.ProductType.TRAILER,
        registration_number="DK-TRAIL-PROD",
        contract_status=Contract.Status.ISSUED,
        payment_status=Payment.Status.CONFIRMED,
        amount=Decimal("5000.00"),
        commission_amount=Decimal("500.00"),
        created_at=_aware(2026, 5, 29),
        contract_number="ASS-TRAILER-PROD-001",
        attestation_reference="SNTRAILPROD",
        attestation_url="https://documents.example.test/trailer/attestation.pdf",
        carte_brune_url="https://documents.example.test/trailer/carte-brune.pdf",
        ass_product_data={"referenceVehicule": contract_auto.contract_number},
    )
    contract_group_b = _contract(
        group=group_b,
        contributor=contributor_b,
        client=client_b,
        product_type=Quote.ProductType.AUTO,
        registration_number="DK-PROD-999",
        contract_status=Contract.Status.ISSUED,
        payment_status=Payment.Status.CONFIRMED,
        amount=Decimal("60000.00"),
        commission_amount=Decimal("0.00"),
        created_at=_aware(2026, 5, 29),
        contract_number="ASS-AUTO-PROD-999",
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
        "contract_auto": contract_auto,
        "contract_pending": contract_pending,
        "contract_failed": contract_failed,
        "contract_other_contributor": contract_other_contributor,
        "contract_trailer": contract_trailer,
        "contract_group_b": contract_group_b,
    }


def _client(group, contributor, first_name, last_name, phone):
    return Client.objects.create(
        partner_group=group,
        contributor=contributor,
        created_by=contributor,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
    )


def _contract(
    *,
    group,
    contributor,
    client,
    product_type,
    registration_number,
    contract_status,
    payment_status,
    amount,
    commission_amount,
    created_at,
    contract_number="",
    attestation_reference="",
    attestation_url="",
    carte_brune_url="",
    ass_product_data=None,
):
    vehicle = Vehicle.objects.create(
        partner_group=group,
        client=client,
        contributor=contributor,
        created_by=contributor,
        registration_number=registration_number,
        brand="Toyota",
        model="Yaris",
        genre="REMORQUE" if product_type == Quote.ProductType.TRAILER else "VP",
        energy=Vehicle.Energy.GASOLINE,
    )
    quote = Quote.objects.create(
        partner_group=group,
        client=client,
        vehicle=vehicle,
        contributor=contributor,
        created_by=contributor,
        product_type=product_type,
        effective_date=date(2026, 5, 29),
        expiration_date=date(2026, 11, 28),
        premium_amount=amount - Decimal("1000.00"),
        fees_amount=Decimal("1000.00"),
        total_amount=amount,
        ass_product_data=ass_product_data or {},
    )
    payment = Payment.objects.create(
        partner_group=group,
        quote=quote,
        client=client,
        contributor=contributor,
        created_by=contributor,
        method=Payment.Method.WAVE,
        status=Payment.Status.CONFIRMED,
        amount=amount,
    )
    contract = Contract.objects.create(
        partner_group=group,
        quote=quote,
        payment=payment,
        client=client,
        vehicle=vehicle,
        contributor=contributor,
        created_by=contributor,
        status=contract_status,
        contract_number=contract_number or None,
        attestation_reference=attestation_reference or None,
        attestation_url=attestation_url,
        carte_brune_url=carte_brune_url,
    )
    Payment.objects.filter(pk=payment.pk).update(status=payment_status)
    Contract.objects.filter(pk=contract.pk).update(created_at=created_at)
    contract.refresh_from_db()
    if commission_amount > Decimal("0.00"):
        Commission.objects.create(
            partner_group=group,
            contract=contract,
            payment=payment,
            contributor=contributor,
            base_amount=amount,
            percentage_rate=Decimal("0.0000"),
            fixed_amount=Decimal("0.00"),
            amount=commission_amount,
            net_to_pay_amount=amount - commission_amount,
        )
    return contract


def _quote_without_contract(
    *,
    group,
    contributor,
    client,
    product_type,
    registration_number,
    amount,
    created_at,
    payment_status="",
):
    vehicle = Vehicle.objects.create(
        partner_group=group,
        client=client,
        contributor=contributor,
        created_by=contributor,
        registration_number=registration_number,
        brand="Nissan",
        model="Qashqai",
        genre="VP",
        energy=Vehicle.Energy.DIESEL,
    )
    quote = Quote.objects.create(
        partner_group=group,
        client=client,
        vehicle=vehicle,
        contributor=contributor,
        created_by=contributor,
        product_type=product_type,
        effective_date=date(2026, 5, 29),
        expiration_date=date(2026, 11, 28),
        premium_amount=amount - Decimal("1000.00"),
        fees_amount=Decimal("1000.00"),
        total_amount=amount,
    )
    Quote.objects.filter(pk=quote.pk).update(created_at=created_at)
    quote.refresh_from_db()
    payment = None
    if payment_status:
        payment = Payment.objects.create(
            partner_group=group,
            quote=quote,
            client=client,
            contributor=contributor,
            created_by=contributor,
            method=Payment.Method.WAVE,
            status=Payment.Status.CONFIRMED,
            amount=amount,
        )
        Payment.objects.filter(pk=payment.pk).update(
            status=payment_status,
            created_at=created_at,
        )
        payment.refresh_from_db()
    return quote, payment


def _aware(year, month, day):
    return timezone.make_aware(
        datetime(year, month, day, 10, 0, 0),
        timezone.get_current_timezone(),
    )


def _client_for(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


def _ids(response):
    return {item["id"] for item in response.data["results"]}


@pytest.mark.django_db
def test_general_admin_sees_all_production(production_context):
    response = _client_for(production_context["general_admin"]).get(
        "/api/v1/production/"
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["scope"] == "platform"
    assert response.data["count"] == 6
    assert _ids(response) == {
        production_context["contract_auto"].id,
        production_context["contract_pending"].id,
        production_context["contract_failed"].id,
        production_context["contract_other_contributor"].id,
        production_context["contract_trailer"].id,
        production_context["contract_group_b"].id,
    }


@pytest.mark.django_db
def test_group_admin_sees_only_group_production(production_context):
    response = _client_for(production_context["group_admin_a"]).get(
        "/api/v1/production/"
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["scope"] == "group"
    assert response.data["count"] == 5
    assert production_context["contract_group_b"].id not in _ids(response)


@pytest.mark.django_db
def test_contributor_sees_only_own_production(production_context):
    response = _client_for(production_context["contributor_a"]).get(
        "/api/v1/production/"
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["scope"] == "contributor"
    assert response.data["count"] == 4
    assert production_context["contract_other_contributor"].id not in _ids(response)
    assert production_context["contract_group_b"].id not in _ids(response)


@pytest.mark.django_db
def test_production_filter_today(production_context, monkeypatch):
    monkeypatch.setattr(
        "apps.common.production._today",
        lambda timezone_info: date(2026, 5, 29),
    )

    response = _client_for(production_context["general_admin"]).get(
        "/api/v1/production/",
        {"today": "true"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert _ids(response) == {
        production_context["contract_auto"].id,
        production_context["contract_trailer"].id,
        production_context["contract_group_b"].id,
    }


@pytest.mark.django_db
def test_production_filter_month(production_context):
    response = _client_for(production_context["general_admin"]).get(
        "/api/v1/production/",
        {"mois": "2026-05"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 5
    assert production_context["contract_failed"].id not in _ids(response)


@pytest.mark.django_db
def test_production_filter_period(production_context):
    response = _client_for(production_context["general_admin"]).get(
        "/api/v1/production/",
        {"date_debut": "2026-04-01", "date_fin": "2026-04-30"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert _ids(response) == {production_context["contract_failed"].id}


@pytest.mark.django_db
def test_production_filter_product(production_context):
    response = _client_for(production_context["general_admin"]).get(
        "/api/v1/production/",
        {"produit": "TRAILER"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert _ids(response) == {production_context["contract_trailer"].id}
    assert response.data["results"][0]["has_trailer"] is True


@pytest.mark.django_db
def test_production_filter_status(production_context):
    response = _client_for(production_context["general_admin"]).get(
        "/api/v1/production/",
        {"contract_status": Contract.Status.ISSUED},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 4
    assert {item["contract_status"] for item in response.data["results"]} == {
        Contract.Status.ISSUED
    }


@pytest.mark.django_db
def test_production_filter_registration_number(production_context):
    response = _client_for(production_context["general_admin"]).get(
        "/api/v1/production/",
        {"immatriculation": "TRAIL"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert _ids(response) == {production_context["contract_trailer"].id}


@pytest.mark.django_db
def test_production_filter_with_trailer(production_context):
    response = _client_for(production_context["general_admin"]).get(
        "/api/v1/production/",
        {"remorque": "true"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert _ids(response) == {production_context["contract_trailer"].id}
    assert response.data["summary"]["contracts_with_trailer"] == 1


@pytest.mark.django_db
def test_production_summary_totals(production_context):
    response = _client_for(production_context["general_admin"]).get(
        "/api/v1/production/"
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["summary"]["total_contracts"] == 6
    assert response.data["summary"]["issued_contracts"] == 4
    assert response.data["summary"]["pending_contracts"] == 1
    assert response.data["summary"]["failed_contracts"] == 1
    assert response.data["summary"]["paid_payments"] == 4
    assert response.data["summary"]["pending_payments"] == 1
    assert response.data["summary"]["failed_payments"] == 1
    assert response.data["summary"]["total_amount"] == "165000.00"
    assert response.data["summary"]["total_paid_amount"] == "115000.00"
    assert response.data["summary"]["total_commission_amount"] == "5500.00"
    assert response.data["summary"]["contracts_with_trailer"] == 1


@pytest.mark.django_db
def test_group_admin_cannot_expand_scope_with_group_filter(production_context):
    response = _client_for(production_context["group_admin_a"]).get(
        "/api/v1/production/",
        {"groupe": production_context["group_b"].id},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 0
    assert response.data["summary"]["total_contracts"] == 0


@pytest.mark.django_db
def test_production_paginates_results(production_context):
    response = _client_for(production_context["general_admin"]).get(
        "/api/v1/production/",
        {"page": 2, "page_size": 2},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 6
    assert len(response.data["results"]) == 2
    assert response.data["pagination"] == {
        "page": 2,
        "page_size": 2,
        "total_count": 6,
        "total_pages": 3,
        "has_next": True,
        "has_previous": True,
        "export": False,
        "max_export_rows": 5000,
        "truncated": False,
    }


@pytest.mark.django_db
def test_production_export_returns_unpaginated_json(production_context):
    response = _client_for(production_context["general_admin"]).get(
        "/api/v1/production/",
        {"export": "true", "page_size": 2},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 6
    assert len(response.data["results"]) == 6
    assert response.data["pagination"]["export"] is True
    assert response.data["pagination"]["truncated"] is False


@pytest.mark.django_db
def test_production_includes_quotes_and_payments_without_contract(production_context):
    quote_only, _ = _quote_without_contract(
        group=production_context["group_a"],
        contributor=production_context["contributor_a"],
        client=production_context["client_a"],
        product_type=Quote.ProductType.AUTO,
        registration_number="DK-QUOTE-ONLY",
        amount=Decimal("7000.00"),
        created_at=_aware(2026, 5, 29),
    )
    quote_with_payment, payment = _quote_without_contract(
        group=production_context["group_a"],
        contributor=production_context["contributor_a"],
        client=production_context["client_a"],
        product_type=Quote.ProductType.MOTO,
        registration_number="DK-PAYMENT-ONLY",
        amount=Decimal("8000.00"),
        created_at=_aware(2026, 5, 29),
        payment_status=Payment.Status.CONFIRMED,
    )

    response = _client_for(production_context["contributor_a"]).get(
        "/api/v1/production/",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["summary"]["total_contracts"] == 4
    assert response.data["summary"]["total_quotes_without_contract"] == 1
    assert response.data["summary"]["total_payments_without_contract"] == 1
    rows = {row["entry_id"]: row for row in response.data["results"]}
    assert rows[f"quote-{quote_only.id}"]["entry_type"] == "QUOTE"
    assert rows[f"quote-{quote_only.id}"]["contract_id"] is None
    assert rows[f"payment-{payment.id}"]["entry_type"] == "PAYMENT"
    assert rows[f"payment-{payment.id}"]["quote_id"] == quote_with_payment.id
    assert rows[f"payment-{payment.id}"]["payment_status"] == Payment.Status.CONFIRMED


@pytest.mark.django_db
def test_production_payment_status_filter_uses_latest_payment(production_context):
    quote, _confirmed_payment = _quote_without_contract(
        group=production_context["group_a"],
        contributor=production_context["contributor_a"],
        client=production_context["client_a"],
        product_type=Quote.ProductType.AUTO,
        registration_number="DK-MULTI-PAY",
        amount=Decimal("9000.00"),
        created_at=_aware(2026, 5, 28),
        payment_status=Payment.Status.CONFIRMED,
    )
    latest_payment = Payment.objects.create(
        partner_group=production_context["group_a"],
        quote=quote,
        client=production_context["client_a"],
        contributor=production_context["contributor_a"],
        created_by=production_context["contributor_a"],
        method=Payment.Method.WAVE,
        status=Payment.Status.FAILED,
        amount=quote.total_amount,
    )
    Payment.objects.filter(pk=latest_payment.pk).update(
        created_at=_aware(2026, 5, 30),
    )
    latest_payment.refresh_from_db()

    confirmed_response = _client_for(production_context["contributor_a"]).get(
        "/api/v1/production/",
        {
            "payment_status": Payment.Status.CONFIRMED,
            "immatriculation": "MULTI-PAY",
        },
    )
    failed_response = _client_for(production_context["contributor_a"]).get(
        "/api/v1/production/",
        {
            "payment_status": Payment.Status.FAILED,
            "immatriculation": "MULTI-PAY",
        },
    )

    assert confirmed_response.status_code == status.HTTP_200_OK
    assert confirmed_response.data["count"] == 0
    assert failed_response.status_code == status.HTTP_200_OK
    assert failed_response.data["count"] == 1
    row = failed_response.data["results"][0]
    assert row["entry_id"] == f"payment-{latest_payment.id}"
    assert row["payment_status"] == Payment.Status.FAILED


@pytest.mark.django_db
def test_production_today_filter_uses_payment_date_for_payments_without_contract(
    production_context,
    monkeypatch,
):
    monkeypatch.setattr(
        "apps.common.production._today",
        lambda timezone_info: date(2026, 5, 29),
    )
    _current_quote, current_payment = _quote_without_contract(
        group=production_context["group_a"],
        contributor=production_context["contributor_a"],
        client=production_context["client_a"],
        product_type=Quote.ProductType.MOTO,
        registration_number="DK-PAYMENT-CURRENT",
        amount=Decimal("8000.00"),
        created_at=_aware(2026, 5, 1),
        payment_status=Payment.Status.CONFIRMED,
    )
    Payment.objects.filter(pk=current_payment.pk).update(
        created_at=_aware(2026, 5, 29),
    )
    current_payment.refresh_from_db()
    _old_quote, old_payment = _quote_without_contract(
        group=production_context["group_a"],
        contributor=production_context["contributor_a"],
        client=production_context["client_a"],
        product_type=Quote.ProductType.AUTO,
        registration_number="DK-PAYMENT-OLD",
        amount=Decimal("7000.00"),
        created_at=_aware(2026, 5, 29),
        payment_status=Payment.Status.CONFIRMED,
    )
    Payment.objects.filter(pk=old_payment.pk).update(created_at=_aware(2026, 5, 1))

    current_response = _client_for(production_context["contributor_a"]).get(
        "/api/v1/production/",
        {"today": "true", "immatriculation": "PAYMENT-CURRENT"},
    )
    old_response = _client_for(production_context["contributor_a"]).get(
        "/api/v1/production/",
        {"today": "true", "immatriculation": "PAYMENT-OLD"},
    )

    assert current_response.status_code == status.HTTP_200_OK
    assert current_response.data["count"] == 1
    assert current_response.data["results"][0]["entry_id"] == (
        f"payment-{current_payment.id}"
    )
    assert old_response.status_code == status.HTTP_200_OK
    assert old_response.data["count"] == 0


@pytest.mark.django_db
def test_production_today_filter_uses_requested_timezone(
    production_context,
    monkeypatch,
):
    Contract.objects.filter(pk=production_context["contract_auto"].pk).update(
        created_at=datetime(2026, 5, 28, 22, 30, tzinfo=UTC)
    )
    monkeypatch.setattr(
        "apps.common.production._today",
        lambda timezone_info: date(2026, 5, 29),
    )

    istanbul_response = _client_for(production_context["general_admin"]).get(
        "/api/v1/production/",
        {
            "today": "true",
            "timezone": "Europe/Istanbul",
            "immatriculation": "DK-PROD-001",
        },
    )
    dakar_response = _client_for(production_context["general_admin"]).get(
        "/api/v1/production/",
        {
            "today": "true",
            "timezone": "Africa/Dakar",
            "immatriculation": "DK-PROD-001",
        },
    )

    assert istanbul_response.status_code == status.HTTP_200_OK
    assert dakar_response.status_code == status.HTTP_200_OK
    assert istanbul_response.data["filters"]["timezone"] == "Europe/Istanbul"
    assert _ids(istanbul_response) == {production_context["contract_auto"].id}
    assert _ids(dakar_response) == set()
