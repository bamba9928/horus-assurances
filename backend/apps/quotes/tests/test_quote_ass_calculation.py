import json
from decimal import Decimal
from io import StringIO
from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings
from rest_framework import serializers, status
from rest_framework.test import APIClient

from apps.clients.models import Client
from apps.groups.models import PartnerGroup
from apps.quotes.ass_payloads import build_ass_rc_payload, build_ass_rc_payload_for_product
from apps.quotes.models import Quote
from apps.quotes.services import calculate_quote_with_ass, extract_ass_rc_amounts
from apps.vehicles.models import Vehicle

User = get_user_model()
FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"


class FakeASSClient:
    def __init__(self, response_payload):
        self.response_payload = response_payload
        self.calls = []

    def calculate_rc(self, payload, *, partner_group=None, contract=None):
        self.calls.append(
            {
                "payload": payload,
                "partner_group": partner_group,
                "contract": contract,
            }
        )
        return self.response_payload


class RecordingASSClient:
    def __init__(self, response_payload=None):
        self.response_payload = response_payload or {
            "data": {
                "responsabiliteCivile": "18688",
                "primeNette": "25000",
                "cout_police": "3000",
                "primeTTC": "28000",
            }
        }
        self.calls = []

    def _record(self, method_name, payload, *, partner_group=None, contract=None):
        self.calls.append(
            {
                "method": method_name,
                "payload": payload,
                "partner_group": partner_group,
                "contract": contract,
            }
        )
        return self.response_payload

    def calculate_rc(self, payload, *, partner_group=None, contract=None):
        return self._record(
            "calculate_rc",
            payload,
            partner_group=partner_group,
            contract=contract,
        )

    def calculate_moto_rc(self, payload, *, partner_group=None, contract=None):
        return self._record(
            "calculate_moto_rc",
            payload,
            partner_group=partner_group,
            contract=contract,
        )

    def calculate_fleet_rc(self, payload, *, partner_group=None, contract=None):
        return self._record(
            "calculate_fleet_rc",
            payload,
            partner_group=partner_group,
            contract=contract,
        )

    def calculate_trailer_rc(self, payload, *, partner_group=None, contract=None):
        return self._record(
            "calculate_trailer_rc",
            payload,
            partner_group=partner_group,
            contract=contract,
        )

    def calculate_school_bus_rc(self, payload, *, partner_group=None, contract=None):
        return self._record(
            "calculate_school_bus_rc",
            payload,
            partner_group=partner_group,
            contract=contract,
        )

    def calculate_garage_rc(self, payload, *, partner_group=None, contract=None):
        return self._record(
            "calculate_garage_rc",
            payload,
            partner_group=partner_group,
            contract=contract,
        )


@pytest.fixture
def ass_quote_context():
    group = PartnerGroup.objects.create(name="ASS Quotes", slug="ass-quotes")
    contributor = User.objects.create_user(
        username="ass-quote-apporteur",
        password="password",
        role=User.Role.CONTRIBUTOR,
        partner_group=group,
    )
    client = Client.objects.create(
        partner_group=group,
        contributor=contributor,
        created_by=contributor,
        first_name="Awa",
        last_name="Fall",
        email="awa@example.com",
        phone="771234567",
    )
    vehicle = Vehicle.objects.create(
        partner_group=group,
        client=client,
        contributor=contributor,
        created_by=contributor,
        registration_number="DK-ASS-01",
        brand="Toyota",
        model="Yaris",
        chassis_number="CH-ASS-01",
        genre="VP",
        energy=Vehicle.Energy.GASOLINE,
        fiscal_power=8,
        seats=5,
        new_value=Decimal("9000900.00"),
        current_value=Decimal("3500000.00"),
    )
    quote = Quote.objects.create(
        partner_group=group,
        client=client,
        vehicle=vehicle,
        contributor=contributor,
        created_by=contributor,
        duration=3,
        coverage_options=[1, 2],
        fees_amount=Decimal("3000.00"),
        premium_amount=Decimal("0.00"),
        total_amount=Decimal("3000.00"),
    )
    return {
        "group": group,
        "contributor": contributor,
        "quote": quote,
    }


@pytest.mark.django_db
def test_build_ass_rc_payload_uses_quote_vehicle_data(ass_quote_context):
    Quote.objects.filter(pk=ass_quote_context["quote"].pk).update(
        ass_product_data={
            "garantiesOptPT": "OPTION_1",
            "garantiesOptAR": "500000",
            "garantiesOptAS": "OPTION_1",
        }
    )
    ass_quote_context["quote"].refresh_from_db()

    payload = build_ass_rc_payload(
        ass_quote_context["quote"],
        rc_discount_amount=Decimal("500.00"),
    )

    assert payload == {
        "puissanceFiscale": 8,
        "duree": 3,
        "genre": "VP",
        "nombrePlace": 5,
        "periodicite": "MOIS",
        "energie": "ESSENCE",
        "valeurNeuve": 9000900,
        "valeurActuelle": 3500000,
        "garanties": [1, 2],
        "garantiesOptPT": "OPTION_1",
        "garantiesOptAR": "500000",
        "garantiesOptAS": "OPTION_1",
        "cout_police": 3000,
        "remise_rc": 500,
    }


@pytest.mark.django_db
def test_build_ass_rc_payload_for_moto_uses_product_data(ass_quote_context):
    Quote.objects.filter(pk=ass_quote_context["quote"].pk).update(
        product_type=Quote.ProductType.MOTO,
        ass_product_data={
            "cylindre": 126,
            "usage": "NON_COMMERCIAL",
        },
    )
    ass_quote_context["quote"].refresh_from_db()

    payload = build_ass_rc_payload_for_product(ass_quote_context["quote"])

    assert payload["cylindre"] == 126
    assert payload["usage"] == "NON_COMMERCIAL"
    assert payload["nombrePlace"] == 5
    assert payload["genre"] == "VP"


@pytest.mark.django_db
def test_build_ass_rc_payload_for_school_bus_uses_vehicle_data(ass_quote_context):
    Vehicle.objects.filter(pk=ass_quote_context["quote"].vehicle_id).update(
        genre="BE-VTA",
        fiscal_power=20,
        seats=30,
        new_value=Decimal("45000000.00"),
        current_value=Decimal("35000000.00"),
    )
    Quote.objects.filter(pk=ass_quote_context["quote"].pk).update(
        product_type=Quote.ProductType.SCHOOL_BUS,
        coverage_options=[],
    )
    ass_quote_context["quote"].refresh_from_db()

    payload = build_ass_rc_payload_for_product(
        ass_quote_context["quote"],
        rc_discount_amount=Decimal("500.00"),
    )

    assert payload == {
        "duree": 3,
        "energie": "ESSENCE",
        "periodicite": "MOIS",
        "genre": "BE-VTA",
        "nombrePlace": 30,
        "puissanceFiscale": 20,
        "cout_police": 3000,
        "remise_rc": 500,
        "valeurNeuve": 45000000,
        "valeurActuelle": 35000000,
        "garanties": [],
    }


@pytest.mark.django_db
def test_build_ass_rc_payload_for_trailer_requires_reference_vehicle(
    ass_quote_context,
):
    Quote.objects.filter(pk=ass_quote_context["quote"].pk).update(
        product_type=Quote.ProductType.TRAILER,
        ass_product_data={},
    )
    ass_quote_context["quote"].refresh_from_db()

    with pytest.raises(serializers.ValidationError):
        build_ass_rc_payload_for_product(ass_quote_context["quote"])


def test_extract_ass_rc_amounts_accepts_nested_ass_response():
    amounts = extract_ass_rc_amounts(
        {
            "data": {
                "responsabiliteCivile": "18688",
                "primeNette": "25000",
                "cout_police": "3000",
                "primeTTC": "28000",
            }
        },
        default_fees_amount=Decimal("0.00"),
    )

    assert amounts == {
        "civil_liability_amount": Decimal("18688.00"),
        "premium_amount": Decimal("25000.00"),
        "fees_amount": Decimal("3000.00"),
        "total_amount": Decimal("28000.00"),
    }


def test_extract_ass_rc_amounts_matches_real_mono_success_fixture():
    fixture = json.loads((FIXTURE_DIR / "ass_rc_mono_success.json").read_text())

    assert fixture["status_code"] == 201
    assert fixture["body"]["operationStatus"] == "SUCCESS"

    amounts = extract_ass_rc_amounts(
        fixture["body"],
        default_fees_amount=Decimal("0.00"),
    )

    assert amounts == {
        "civil_liability_amount": Decimal("13708.00"),
        "premium_amount": Decimal("22624.00"),
        "fees_amount": Decimal("3000.00"),
        "total_amount": Decimal("25624.00"),
    }
    assert amounts["premium_amount"] + amounts["fees_amount"] == amounts["total_amount"]


@pytest.mark.django_db
def test_calculate_quote_with_ass_updates_amounts_and_status(ass_quote_context):
    fake_client = FakeASSClient(
        {
            "data": {
                "responsabiliteCivile": "18688",
                "primeNette": "25000",
                "cout_police": "3000",
                "primeTTC": "28000",
            }
        }
    )

    quote = calculate_quote_with_ass(
        quote=ass_quote_context["quote"],
        calculation_values={
            "coverage_options": [1, 2, 4],
            "fees_amount": Decimal("3000.00"),
        },
        rc_discount_amount=Decimal("0.00"),
        client=fake_client,
    )

    assert quote.status == Quote.Status.CALCULATED
    assert quote.civil_liability_amount == Decimal("18688.00")
    assert quote.premium_amount == Decimal("25000.00")
    assert quote.fees_amount == Decimal("3000.00")
    assert quote.total_amount == Decimal("28000.00")
    assert quote.coverage_options == [1, 2, 4]
    assert fake_client.calls[0]["partner_group"] == ass_quote_context["group"]
    assert fake_client.calls[0]["payload"]["garanties"] == [1, 2, 4]


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("product_type", "method_name", "ass_product_data"),
    [
        (Quote.ProductType.AUTO, "calculate_rc", {}),
        (
            Quote.ProductType.MOTO,
            "calculate_moto_rc",
            {"cylindre": 126, "usage": "NON_COMMERCIAL"},
        ),
        (Quote.ProductType.FLEET, "calculate_fleet_rc", {}),
        (
            Quote.ProductType.TRAILER,
            "calculate_trailer_rc",
            {"referenceVehicule": "DK-TRACT-001"},
        ),
        (Quote.ProductType.SCHOOL_BUS, "calculate_school_bus_rc", {}),
        (
            Quote.ProductType.GARAGE,
            "calculate_garage_rc",
            {"nombreCarte": 2},
        ),
    ],
)
def test_calculate_quote_with_ass_routes_rc_by_product_type(
    ass_quote_context,
    product_type,
    method_name,
    ass_product_data,
):
    Quote.objects.filter(pk=ass_quote_context["quote"].pk).update(
        product_type=product_type,
        ass_product_data=ass_product_data,
    )
    ass_quote_context["quote"].refresh_from_db()
    ass_client = RecordingASSClient()

    quote = calculate_quote_with_ass(
        quote=ass_quote_context["quote"],
        client=ass_client,
    )

    assert quote.status == Quote.Status.CALCULATED
    assert ass_client.calls[0]["method"] == method_name
    assert ass_client.calls[0]["partner_group"] == ass_quote_context["group"]


@pytest.mark.django_db
def test_calculate_quote_with_ass_rejects_empty_ass_amounts_without_persisting(
    ass_quote_context,
):
    fake_client = FakeASSClient({"data": {"message": "aucun montant"}})

    with pytest.raises(serializers.ValidationError):
        calculate_quote_with_ass(
            quote=ass_quote_context["quote"],
            calculation_values={
                "coverage_options": [4],
                "fees_amount": Decimal("5000.00"),
            },
            client=fake_client,
        )

    ass_quote_context["quote"].refresh_from_db()
    assert ass_quote_context["quote"].status == Quote.Status.DRAFT
    assert ass_quote_context["quote"].coverage_options == [1, 2]
    assert ass_quote_context["quote"].fees_amount == Decimal("3000.00")


@pytest.mark.django_db
def test_quote_calculate_action_can_use_ass_service(ass_quote_context, monkeypatch):
    def fake_calculate_quote_with_ass(*, quote, calculation_values, rc_discount_amount):
        quote.coverage_options = calculation_values["coverage_options"]
        quote.civil_liability_amount = Decimal("18688.00")
        quote.premium_amount = Decimal("25000.00")
        quote.fees_amount = Decimal("3000.00")
        quote.total_amount = Decimal("28000.00")
        quote.status = Quote.Status.CALCULATED
        quote.save()
        return quote

    monkeypatch.setattr(
        "apps.quotes.views.calculate_quote_with_ass",
        fake_calculate_quote_with_ass,
    )
    client = APIClient()
    client.force_authenticate(ass_quote_context["contributor"])

    response = client.post(
        f"/api/v1/quotes/{ass_quote_context['quote'].id}/calculate/",
        {
            "use_ass": True,
            "coverage_options": [1, 2, 4],
            "fees_amount": "3000.00",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["status"] == Quote.Status.CALCULATED
    assert response.data["civil_liability_amount"] == "18688.00"
    assert response.data["total_amount"] == "28000.00"


@pytest.mark.django_db
def test_validate_ass_sandbox_quote_command_previews_without_external_call(
    ass_quote_context,
):
    Quote.objects.filter(pk=ass_quote_context["quote"].pk).update(
        product_type=Quote.ProductType.SCHOOL_BUS,
    )
    output = StringIO()

    call_command(
        "validate_ass_sandbox_quote_calculation",
        ass_quote_context["quote"].id,
        stdout=output,
    )

    command_output = output.getvalue()
    assert "ass_payload_preview" in command_output
    assert "/api/v1/partner/bus.ecole.rc" in command_output
    assert "Aucun appel externe ASS effectue" in command_output


@pytest.mark.django_db
@override_settings(ASS_BASE_URL="https://manager.example.com")
def test_validate_ass_sandbox_quote_command_blocks_non_sandbox_url(
    ass_quote_context,
    monkeypatch,
):
    class FailingASSClient:
        def calculate_school_bus_rc(self, payload, *, partner_group=None, contract=None):
            raise AssertionError("external ASS call should not be made")

    monkeypatch.setattr(
        "apps.quotes.management.commands.validate_ass_sandbox_quote_calculation.ASSAPIClient",
        FailingASSClient,
    )
    Quote.objects.filter(pk=ass_quote_context["quote"].pk).update(
        product_type=Quote.ProductType.SCHOOL_BUS,
    )

    with pytest.raises(CommandError, match="ne ressemble pas a une sandbox"):
        call_command(
            "validate_ass_sandbox_quote_calculation",
            ass_quote_context["quote"].id,
            "--confirm-external-ass-call",
            stdout=StringIO(),
        )


@pytest.mark.django_db
@override_settings(ASS_BASE_URL="https://kiiraytest.example.com")
def test_validate_ass_sandbox_quote_command_calls_ass_without_persisting(
    ass_quote_context,
    monkeypatch,
):
    class FakeASSClient:
        calls = []

        def calculate_school_bus_rc(self, payload, *, partner_group=None, contract=None):
            self.__class__.calls.append(
                {
                    "payload": payload,
                    "partner_group": partner_group,
                    "contract": contract,
                }
            )
            return {
                "code": 2000,
                "operationStatus": "SUCCESS",
                "operationMessage": "Operation effectuee avec succes.",
                "data": 391193,
            }

    monkeypatch.setattr(
        "apps.quotes.management.commands.validate_ass_sandbox_quote_calculation.ASSAPIClient",
        FakeASSClient,
    )
    Quote.objects.filter(pk=ass_quote_context["quote"].pk).update(
        product_type=Quote.ProductType.SCHOOL_BUS,
    )
    output = StringIO()

    call_command(
        "validate_ass_sandbox_quote_calculation",
        ass_quote_context["quote"].id,
        "--confirm-external-ass-call",
        stdout=output,
    )

    ass_quote_context["quote"].refresh_from_db()
    command_output = output.getvalue()
    assert FakeASSClient.calls[0]["partner_group"] == ass_quote_context["group"]
    assert FakeASSClient.calls[0]["contract"] is None
    assert FakeASSClient.calls[0]["payload"]["duree"] == 3
    assert '"persisted_quote_calculation": false' in command_output
    assert ass_quote_context["quote"].status == Quote.Status.DRAFT
    assert ass_quote_context["quote"].civil_liability_amount == Decimal("0.00")
