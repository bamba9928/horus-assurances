from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.clients.models import Client
from apps.commissions.models import CommissionRule
from apps.contracts.models import Contract
from apps.groups.models import PartnerGroup
from apps.payments.models import Payment
from apps.quotes.models import Quote
from apps.reference_data.models import (
    DurationOption,
    EnergyType,
    GuaranteeReference,
    ProductReference,
    VehicleBrand,
    VehicleGenre,
)
from apps.vehicles.models import Vehicle

User = get_user_model()


@pytest.fixture
def quote_summary_context():
    group_a = PartnerGroup.objects.create(name="Summary Groupe A", slug="summary-a")
    group_b = PartnerGroup.objects.create(name="Summary Groupe B", slug="summary-b")
    general_admin = User.objects.create_user(
        username="summary-general",
        password="password",
        role=User.Role.GENERAL_ADMIN,
    )
    group_admin_a = User.objects.create_user(
        username="summary-admin-a",
        password="password",
        role=User.Role.GROUP_ADMIN,
        partner_group=group_a,
    )
    contributor_a = User.objects.create_user(
        username="summary-apporteur-a",
        password="password",
        role=User.Role.CONTRIBUTOR,
        partner_group=group_a,
    )
    contributor_a2 = User.objects.create_user(
        username="summary-apporteur-a2",
        password="password",
        role=User.Role.CONTRIBUTOR,
        partner_group=group_a,
    )
    contributor_b = User.objects.create_user(
        username="summary-apporteur-b",
        password="password",
        role=User.Role.CONTRIBUTOR,
        partner_group=group_b,
    )

    client_a = Client.objects.create(
        partner_group=group_a,
        contributor=contributor_a,
        created_by=contributor_a,
        first_name="Awa",
        last_name="Summary",
        email="awa.summary@example.test",
        phone="771110001",
    )
    client_a2 = Client.objects.create(
        partner_group=group_a,
        contributor=contributor_a2,
        created_by=contributor_a2,
        first_name="Aminata",
        last_name="Summary",
        phone="771110002",
    )
    client_b = Client.objects.create(
        partner_group=group_b,
        contributor=contributor_b,
        created_by=contributor_b,
        first_name="Baba",
        last_name="Summary",
        phone="771110003",
    )

    GuaranteeReference.objects.filter(code="INCENDIE").update(ass_id=4)

    vehicle_with_refs = Vehicle.objects.create(
        partner_group=group_a,
        client=client_a,
        contributor=contributor_a,
        created_by=contributor_a,
        registration_number="DK-SUM-FK",
        brand="Legacy Brand",
        brand_reference=VehicleBrand.objects.get(code="TOYOTA"),
        model="Yaris",
        genre="LEGACY_GENRE",
        genre_reference=VehicleGenre.objects.get(code="TPC_MOINS_3T500"),
        energy=Vehicle.Energy.DIESEL,
        energy_reference=EnergyType.objects.get(code="ESSENCE"),
        fiscal_power=8,
        seats=5,
        new_value=Decimal("9000000.00"),
        current_value=Decimal("3500000.00"),
    )
    quote_with_refs = Quote.objects.create(
        partner_group=group_a,
        client=client_a,
        vehicle=vehicle_with_refs,
        contributor=contributor_a,
        created_by=contributor_a,
        product_type=Quote.ProductType.GARAGE,
        product_reference=ProductReference.objects.get(code="AUTO"),
        duration=12,
        duration_option=DurationOption.objects.get(code="6_MONTHS"),
        periodicity=Quote.Periodicity.YEARS,
        effective_date=date(2026, 5, 28),
        coverage_options=[4],
        civil_liability_amount=Decimal("18688.00"),
        premium_amount=Decimal("50000.00"),
        fees_amount=Decimal("5000.00"),
        total_amount=Decimal("55000.00"),
    )
    Payment.objects.create(
        partner_group=group_a,
        quote=quote_with_refs,
        client=client_a,
        contributor=contributor_a,
        created_by=contributor_a,
        method=Payment.Method.WAVE,
        status=Payment.Status.CONFIRMED,
        amount=Decimal("55000.00"),
        external_reference="WAVE-SUMMARY-001",
    )
    CommissionRule.objects.create(
        partner_group=group_a,
        contributor=contributor_a,
        percentage_rate=Decimal("10.0000"),
        fixed_amount=Decimal("750.00"),
    )

    vehicle_without_refs = Vehicle.objects.create(
        partner_group=group_a,
        client=client_a2,
        contributor=contributor_a2,
        created_by=contributor_a2,
        registration_number="DK-SUM-TXT",
        brand="Legacy Brand",
        model="Legacy",
        genre="LEGACY_GENRE",
        energy=Vehicle.Energy.DIESEL,
    )
    quote_without_refs = Quote.objects.create(
        partner_group=group_a,
        client=client_a2,
        vehicle=vehicle_without_refs,
        contributor=contributor_a2,
        created_by=contributor_a2,
        product_type=Quote.ProductType.GARAGE,
        duration=3,
        periodicity=Quote.Periodicity.MONTHS,
        civil_liability_amount=Decimal("10000.00"),
        premium_amount=Decimal("15000.00"),
        fees_amount=Decimal("3000.00"),
        total_amount=Decimal("18000.00"),
    )

    vehicle_b = Vehicle.objects.create(
        partner_group=group_b,
        client=client_b,
        contributor=contributor_b,
        created_by=contributor_b,
        registration_number="DK-SUM-B",
        brand="Kia",
        model="Rio",
        genre="VP",
        energy=Vehicle.Energy.GASOLINE,
    )
    quote_b = Quote.objects.create(
        partner_group=group_b,
        client=client_b,
        vehicle=vehicle_b,
        contributor=contributor_b,
        created_by=contributor_b,
        premium_amount=Decimal("20000.00"),
        fees_amount=Decimal("3000.00"),
        total_amount=Decimal("23000.00"),
    )

    return {
        "group_a": group_a,
        "general_admin": general_admin,
        "group_admin_a": group_admin_a,
        "contributor_a": contributor_a,
        "contributor_a2": contributor_a2,
        "client_a": client_a,
        "quote_with_refs": quote_with_refs,
        "quote_without_refs": quote_without_refs,
        "quote_b": quote_b,
    }


def _api_client(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.mark.django_db
def test_quote_summary_uses_reference_fks_and_commission(quote_summary_context):
    client = _api_client(quote_summary_context["general_admin"])

    response = client.get(
        f"/api/v1/quotes/{quote_summary_context['quote_with_refs'].id}/summary/"
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["client"]["display_name"] == "Awa Summary"
    assert response.data["vehicle"]["registration_number"] == "DK-SUM-FK"
    assert response.data["references"]["brand"]["source"] == "reference"
    assert response.data["references"]["brand"]["value"] == "TOYOTA"
    assert response.data["references"]["genre"]["source"] == "reference"
    assert response.data["references"]["genre"]["value"] == "TPC moins de 3t500"
    assert response.data["references"]["energy"]["value"] == "ESSENCE"
    assert response.data["references"]["product"]["code"] == "AUTO"
    assert response.data["references"]["duration"]["code"] == "6_MONTHS"
    assert response.data["validity"] == {
        "effective_date": "2026-05-28",
        "expiration_date": "2026-11-27",
        "expiration_source": "calculated",
        "duration": 6,
        "periodicity": "MOIS",
    }
    assert response.data["payment"]["status"] == Payment.Status.CONFIRMED
    assert response.data["amounts"]["civil_liability_amount"] == "18688.00"
    assert response.data["amounts"]["fees_amount"] == "5000.00"
    assert response.data["amounts"]["contributor_commission_amount"] == "5750.00"
    assert response.data["amounts"]["commission_total_amount"] == "5750.00"
    assert response.data["amounts"]["net_to_pay_after_commission"] == "49250.00"
    assert response.data["amounts"]["total_to_pay"] == "55000.00"
    assert response.data["trailer_rule"]["visible"] is True
    assert response.data["trailer_rule"]["source"] == "form_rule"
    assert response.data["can_issue"]["allowed"] is True
    assert response.data["can_issue"]["requires_contract_creation"] is True


@pytest.mark.django_db
def test_quote_summary_keeps_legacy_fallbacks_without_reference_fks(
    quote_summary_context,
):
    client = _api_client(quote_summary_context["general_admin"])

    response = client.get(
        f"/api/v1/quotes/{quote_summary_context['quote_without_refs'].id}/summary/"
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["references"]["brand"] == {
        "id": None,
        "code": "Legacy Brand",
        "ass_code": "",
        "label": "Legacy Brand",
        "value": "Legacy Brand",
        "source": "legacy",
    }
    assert response.data["references"]["genre"]["source"] == "legacy"
    assert response.data["references"]["genre"]["value"] == "LEGACY_GENRE"
    assert response.data["references"]["energy"]["source"] == "legacy"
    assert response.data["references"]["energy"]["value"] == Vehicle.Energy.DIESEL
    assert response.data["references"]["product"]["source"] == "legacy"
    assert response.data["references"]["product"]["value"] == Quote.ProductType.GARAGE
    assert response.data["references"]["duration"]["source"] == "legacy"
    assert response.data["references"]["duration"]["duration"] == 3
    assert response.data["trailer_rule"]["visible"] is False
    assert response.data["can_issue"]["allowed"] is False
    assert "Aucun paiement" in response.data["can_issue"]["reasons"][0]


@pytest.mark.django_db
def test_quote_summary_exposes_mandatory_and_optional_guarantees(
    quote_summary_context,
):
    client = _api_client(quote_summary_context["general_admin"])

    response = client.get(
        f"/api/v1/quotes/{quote_summary_context['quote_with_refs'].id}/summary/"
    )

    assert response.status_code == status.HTTP_200_OK
    mandatory = {
        guarantee["code"]: guarantee for guarantee in response.data["guarantees"]["mandatory"]
    }
    assert {"RC", "CEDEAO"}.issubset(mandatory)
    for code in ("RC", "CEDEAO"):
        assert mandatory[code]["is_mandatory"] is True
        assert mandatory[code]["selected"] is True
        assert mandatory[code]["is_readonly"] is True

    optional = {
        guarantee["code"]: guarantee for guarantee in response.data["guarantees"]["optional"]
    }
    assert optional["INCENDIE"]["selected"] is True
    assert optional["INCENDIE"]["ass_id"] == 4
    assert response.data["guarantees"]["selected_coverage_options"] == [4]


@pytest.mark.django_db
def test_quote_summary_exposes_four_expected_documents_for_trailer(
    quote_summary_context,
):
    quote_with_refs = quote_summary_context["quote_with_refs"]
    payment = Payment.objects.get(quote=quote_with_refs)
    Contract.objects.create(
        partner_group=quote_summary_context["group_a"],
        quote=quote_with_refs,
        payment=payment,
        client=quote_summary_context["client_a"],
        vehicle=quote_with_refs.vehicle,
        contributor=quote_summary_context["contributor_a"],
        created_by=quote_summary_context["contributor_a"],
        status=Contract.Status.ISSUED,
        contract_number="ASS-AUTO-SUMMARY-001",
        attestation_reference="SNSUMTRACT",
        attestation_url="https://diotali.example.test/attestation/SNSUMTRACT",
        carte_brune_url="https://diotali.example.test/carte-brune/SNSUMTRACT",
    )
    trailer_vehicle = Vehicle.objects.create(
        partner_group=quote_summary_context["group_a"],
        client=quote_summary_context["client_a"],
        contributor=quote_summary_context["contributor_a"],
        created_by=quote_summary_context["contributor_a"],
        registration_number="DK-SUM-REM",
        brand="Remorque",
        model="Plateau",
        genre="REMORQUE",
        energy=Vehicle.Energy.GASOLINE,
    )
    trailer_quote = Quote.objects.create(
        partner_group=quote_summary_context["group_a"],
        client=quote_summary_context["client_a"],
        vehicle=trailer_vehicle,
        contributor=quote_summary_context["contributor_a"],
        created_by=quote_summary_context["contributor_a"],
        product_type=Quote.ProductType.TRAILER,
        ass_product_data={"referenceVehicule": "ASS-AUTO-SUMMARY-001"},
        premium_amount=Decimal("5000.00"),
        fees_amount=Decimal("1000.00"),
        total_amount=Decimal("6000.00"),
    )
    client = _api_client(quote_summary_context["general_admin"])

    response = client.get(f"/api/v1/quotes/{trailer_quote.id}/summary/")

    assert response.status_code == status.HTTP_200_OK
    assert [document["code"] for document in response.data["expected_documents"]] == [
        "TRACTOR_ATTESTATION",
        "TRACTOR_CARTE_BRUNE",
        "TRAILER_ATTESTATION",
        "TRAILER_CARTE_BRUNE",
    ]
    assert response.data["expected_documents"][0]["available"] is True
    assert response.data["expected_documents"][1]["available"] is True
    assert response.data["expected_documents"][2]["available"] is False
    assert response.data["expected_documents"][3]["available"] is False


@pytest.mark.django_db
def test_quote_summary_permissions_respect_group_and_contributor_scope(
    quote_summary_context,
):
    group_admin = _api_client(quote_summary_context["group_admin_a"])
    contributor = _api_client(quote_summary_context["contributor_a"])

    other_group_response = group_admin.get(
        f"/api/v1/quotes/{quote_summary_context['quote_b'].id}/summary/"
    )
    other_contributor_response = contributor.get(
        f"/api/v1/quotes/{quote_summary_context['quote_without_refs'].id}/summary/"
    )

    assert other_group_response.status_code == status.HTTP_404_NOT_FOUND
    assert other_contributor_response.status_code == status.HTTP_404_NOT_FOUND
