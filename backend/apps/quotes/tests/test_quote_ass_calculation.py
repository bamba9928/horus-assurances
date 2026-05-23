import json
from decimal import Decimal
from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from rest_framework import serializers, status
from rest_framework.test import APIClient

from apps.clients.models import Client
from apps.groups.models import PartnerGroup
from apps.quotes.ass_payloads import build_ass_rc_payload
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
        "cout_police": 3000,
        "remise_rc": 500,
    }


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
