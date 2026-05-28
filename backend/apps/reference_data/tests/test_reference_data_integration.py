from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.clients.models import Client
from apps.contracts.ass_payloads import build_ass_qrcode_payload
from apps.contracts.models import Contract
from apps.groups.models import PartnerGroup
from apps.payments.models import Payment
from apps.quotes.ass_payloads import build_ass_rc_payload, build_ass_rc_payload_for_product
from apps.quotes.models import Quote
from apps.quotes.services import build_quote_ass_payload_preview
from apps.reference_data.models import (
    DurationOption,
    EnergyType,
    GuaranteeReference,
    ProductReference,
    VehicleBrand,
    VehicleGenre,
)
from apps.reference_data.services import (
    mandatory_guarantee_references,
    quote_product_code,
)
from apps.vehicles.models import Vehicle

User = get_user_model()


@pytest.fixture
def reference_context():
    group = PartnerGroup.objects.create(name="Reference Integration", slug="reference-int")
    general_admin = User.objects.create_user(
        username="reference-integration-admin",
        password="password",
        role=User.Role.GENERAL_ADMIN,
    )
    contributor = User.objects.create_user(
        username="reference-integration-apporteur",
        password="password",
        role=User.Role.CONTRIBUTOR,
        partner_group=group,
    )
    client = Client.objects.create(
        partner_group=group,
        contributor=contributor,
        created_by=contributor,
        first_name="Reference",
        last_name="Client",
        phone="781111111",
    )
    return {
        "group": group,
        "general_admin": general_admin,
        "contributor": contributor,
        "client": client,
    }


def _api_client(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


def _vehicle(context, **overrides):
    defaults = {
        "partner_group": context["group"],
        "client": context["client"],
        "contributor": context["contributor"],
        "created_by": context["contributor"],
        "registration_number": "DK-REF-001",
        "brand": "Toyota",
        "model": "Yaris",
        "genre": "VP",
        "energy": Vehicle.Energy.GASOLINE,
        "fiscal_power": 8,
        "seats": 5,
        "new_value": Decimal("9000000.00"),
        "current_value": Decimal("3500000.00"),
    }
    defaults.update(overrides)
    return Vehicle.objects.create(**defaults)


def _quote(context, vehicle, **overrides):
    defaults = {
        "partner_group": context["group"],
        "client": context["client"],
        "vehicle": vehicle,
        "contributor": context["contributor"],
        "created_by": context["contributor"],
        "duration": 12,
        "periodicity": Quote.Periodicity.MONTHS,
        "coverage_options": [1, 2],
        "civil_liability_amount": Decimal("18688.00"),
        "premium_amount": Decimal("25000.00"),
        "fees_amount": Decimal("3000.00"),
        "total_amount": Decimal("28000.00"),
    }
    defaults.update(overrides)
    return Quote.objects.create(**defaults)


@pytest.mark.django_db
def test_vehicle_can_be_created_with_reference_fks_and_without_legacy_text(
    reference_context,
):
    client = _api_client(reference_context["general_admin"])
    brand = VehicleBrand.objects.get(code="TOYOTA")
    genre = VehicleGenre.objects.get(code="VP")
    energy = EnergyType.objects.get(code="ESSENCE")

    response = client.post(
        "/api/v1/vehicles/",
        {
            "partner_group": reference_context["group"].id,
            "client": reference_context["client"].id,
            "registration_number": "DK-REF-FK",
            "brand_reference": brand.id,
            "model": "Yaris",
            "genre_reference": genre.id,
            "energy_reference": energy.id,
        },
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED
    vehicle = Vehicle.objects.get(registration_number="DK-REF-FK")
    assert vehicle.brand_reference == brand
    assert vehicle.genre_reference == genre
    assert vehicle.energy_reference == energy
    assert vehicle.brand == "Toyota"
    assert vehicle.genre == "VP"
    assert vehicle.energy == Vehicle.Energy.GASOLINE
    assert response.data["brand_reference_code"] == "TOYOTA"
    assert response.data["genre_reference_code"] == "VP"
    assert response.data["energy_reference_code"] == "ESSENCE"


@pytest.mark.django_db
def test_vehicle_can_still_be_created_with_legacy_text_fallback(reference_context):
    client = _api_client(reference_context["general_admin"])

    response = client.post(
        "/api/v1/vehicles/",
        {
            "partner_group": reference_context["group"].id,
            "client": reference_context["client"].id,
            "registration_number": "DK-REF-TEXT",
            "brand": "Legacy Brand",
            "model": "Legacy",
            "genre": "LEGACY_GENRE",
            "energy": Vehicle.Energy.DIESEL,
        },
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED
    vehicle = Vehicle.objects.get(registration_number="DK-REF-TEXT")
    assert vehicle.brand_reference is None
    assert vehicle.genre_reference is None
    assert vehicle.energy_reference is None
    assert vehicle.brand == "Legacy Brand"
    assert vehicle.genre == "LEGACY_GENRE"
    assert vehicle.energy == Vehicle.Energy.DIESEL


@pytest.mark.django_db
def test_quote_can_be_created_with_product_reference_and_duration_option(
    reference_context,
):
    vehicle = _vehicle(reference_context, registration_number="DK-REF-QFK")
    client = _api_client(reference_context["general_admin"])
    product = ProductReference.objects.get(code="MOTO")
    duration_option = DurationOption.objects.get(code="6_MONTHS")

    response = client.post(
        "/api/v1/quotes/",
        {
            "partner_group": reference_context["group"].id,
            "client": reference_context["client"].id,
            "vehicle": vehicle.id,
            "product_reference": product.id,
            "duration_option": duration_option.id,
            "fees_amount": "3000.00",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED
    quote = Quote.objects.get(id=response.data["id"])
    assert quote.product_reference == product
    assert quote.duration_option == duration_option
    assert quote.product_type == Quote.ProductType.MOTO
    assert quote.duration == 6
    assert quote.periodicity == Quote.Periodicity.MONTHS
    assert response.data["product_reference_code"] == "MOTO"
    assert response.data["duration_option_code"] == "6_MONTHS"


@pytest.mark.django_db
def test_quote_can_still_be_created_with_product_type_fallback(reference_context):
    vehicle = _vehicle(reference_context, registration_number="DK-REF-QTEXT")
    client = _api_client(reference_context["general_admin"])

    response = client.post(
        "/api/v1/quotes/",
        {
            "partner_group": reference_context["group"].id,
            "client": reference_context["client"].id,
            "vehicle": vehicle.id,
            "product_type": Quote.ProductType.GARAGE,
            "duration": 3,
            "periodicity": Quote.Periodicity.MONTHS,
            "fees_amount": "3000.00",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED
    quote = Quote.objects.get(id=response.data["id"])
    assert quote.product_reference is None
    assert quote.duration_option is None
    assert quote.product_type == Quote.ProductType.GARAGE
    assert quote.duration == 3


@pytest.mark.django_db
def test_ass_rc_payload_without_reference_fks_keeps_legacy_payload(reference_context):
    vehicle = _vehicle(reference_context)
    quote = _quote(
        reference_context,
        vehicle,
        duration=3,
        ass_product_data={
            "garantiesOptPT": "OPTION_1",
            "garantiesOptAR": "500000",
            "garantiesOptAS": "OPTION_1",
        },
    )

    payload = build_ass_rc_payload(quote, rc_discount_amount=Decimal("500.00"))

    assert payload == {
        "puissanceFiscale": 8,
        "duree": 3,
        "genre": "VP",
        "nombrePlace": 5,
        "periodicite": "MOIS",
        "energie": "ESSENCE",
        "valeurNeuve": 9000000,
        "valeurActuelle": 3500000,
        "garanties": [1, 2],
        "garantiesOptPT": "OPTION_1",
        "garantiesOptAR": "500000",
        "garantiesOptAS": "OPTION_1",
        "cout_police": 3000,
        "remise_rc": 500,
    }


@pytest.mark.django_db
def test_ass_rc_payload_uses_active_reference_fks_before_legacy_text(reference_context):
    vehicle = _vehicle(
        reference_context,
        registration_number="DK-REF-PAYLOAD-FK",
        brand="Legacy Brand",
        genre="LEGACY_GENRE",
        energy=Vehicle.Energy.DIESEL,
        genre_reference=VehicleGenre.objects.get(code="TPC_MOINS_3T500"),
        energy_reference=EnergyType.objects.get(code="ESSENCE"),
    )
    quote = _quote(
        reference_context,
        vehicle,
        duration=12,
        duration_option=DurationOption.objects.get(code="6_MONTHS"),
    )

    payload = build_ass_rc_payload(quote)

    assert payload["duree"] == 6
    assert payload["periodicite"] == "MOIS"
    assert payload["genre"] == "TPC moins de 3t500"
    assert payload["energie"] == "ESSENCE"


@pytest.mark.django_db
def test_ass_product_payload_routes_with_product_reference(reference_context):
    vehicle = _vehicle(reference_context, registration_number="DK-REF-PRODUCT-FK")
    quote = _quote(
        reference_context,
        vehicle,
        product_type=Quote.ProductType.AUTO,
        product_reference=ProductReference.objects.get(code="MOTO"),
        ass_product_data={
            "cylindre": 126,
            "usage": "NON_COMMERCIAL",
        },
    )

    payload = build_ass_rc_payload_for_product(quote)
    preview = build_quote_ass_payload_preview(quote=quote)

    assert quote_product_code(quote) == Quote.ProductType.MOTO
    assert payload["cylindre"] == 126
    assert preview["product_type"] == Quote.ProductType.MOTO
    assert preview["ass_method"] == "calculate_moto_rc"


@pytest.mark.django_db
def test_ass_qrcode_payload_uses_vehicle_reference_fks(reference_context):
    vehicle = _vehicle(
        reference_context,
        registration_number="DK-REF-QR-FK",
        brand="Legacy Brand",
        genre="LEGACY_GENRE",
        energy=Vehicle.Energy.DIESEL,
        brand_reference=VehicleBrand.objects.get(code="TOYOTA"),
        genre_reference=VehicleGenre.objects.get(code="VP"),
        energy_reference=EnergyType.objects.get(code="ESSENCE"),
    )
    quote = _quote(reference_context, vehicle)
    payment = Payment.objects.create(
        partner_group=reference_context["group"],
        quote=quote,
        client=reference_context["client"],
        contributor=reference_context["contributor"],
        created_by=reference_context["contributor"],
        method=Payment.Method.WAVE,
        status=Payment.Status.CONFIRMED,
        amount=quote.total_amount,
        external_reference="WAVE-REF-001",
    )
    contract = Contract.objects.create(
        partner_group=reference_context["group"],
        quote=quote,
        payment=payment,
        client=reference_context["client"],
        vehicle=vehicle,
        contributor=reference_context["contributor"],
        created_by=reference_context["contributor"],
    )

    payload = build_ass_qrcode_payload(contract)

    assert payload["vehicule"]["marque"] == "TOYOTA"
    assert payload["vehicule"]["genre"] == "VP"
    assert payload["vehicule"]["energie"] == "ESSENCE"


@pytest.mark.django_db
def test_mandatory_guarantee_helpers_keep_rc_and_cedeao_locked():
    guarantees = {guarantee.code: guarantee for guarantee in mandatory_guarantee_references()}

    assert {"RC", "CEDEAO"}.issubset(guarantees)
    for code in ("RC", "CEDEAO"):
        guarantee = guarantees[code]
        assert guarantee.is_mandatory is True
        assert guarantee.is_default_selected is True
        assert guarantee.is_readonly is True
    assert GuaranteeReference.objects.filter(code="RC").count() == 1
    assert GuaranteeReference.objects.filter(code="CEDEAO").count() == 1
