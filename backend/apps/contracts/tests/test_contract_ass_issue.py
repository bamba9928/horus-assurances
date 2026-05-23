from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.clients.models import Client
from apps.contracts.ass_payloads import (
    build_ass_qrcode_payload,
    build_ass_qrcode_payload_for_product,
)
from apps.contracts.models import Contract
from apps.contracts.services import ASSContractIssuer, issue_contract
from apps.groups.models import PartnerGroup
from apps.payments.models import Payment
from apps.quotes.models import Quote
from apps.vehicles.models import Vehicle

User = get_user_model()


class FakeIssuer:
    def __init__(self, response=None, exception=None):
        self.response = response or {
            "contractNumber": "ASS-CONTRACT-123",
            "attestationReference": "ASS-ATT-123",
            "qrCodeReference": "ASS-QR-123",
        }
        self.exception = exception
        self.calls = []

    def issue(self, contract):
        self.calls.append(contract.id)
        if self.exception:
            raise self.exception
        return self.response


class RecordingASSClient:
    def __init__(self):
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
        return {
            "contractNumber": "ASS-CONTRACT-123",
            "attestationReference": "ASS-ATT-123",
            "qrCodeReference": "ASS-QR-123",
        }

    def request_qrcode(self, payload, *, partner_group=None, contract=None):
        return self._record(
            "request_qrcode",
            payload,
            partner_group=partner_group,
            contract=contract,
        )

    def request_moto_qrcode(self, payload, *, partner_group=None, contract=None):
        return self._record(
            "request_moto_qrcode",
            payload,
            partner_group=partner_group,
            contract=contract,
        )

    def request_fleet_qrcode(self, payload, *, partner_group=None, contract=None):
        return self._record(
            "request_fleet_qrcode",
            payload,
            partner_group=partner_group,
            contract=contract,
        )

    def request_trailer_qrcode(self, payload, *, partner_group=None, contract=None):
        return self._record(
            "request_trailer_qrcode",
            payload,
            partner_group=partner_group,
            contract=contract,
        )

    def request_garage_qrcode(self, payload, *, partner_group=None, contract=None):
        return self._record(
            "request_garage_qrcode",
            payload,
            partner_group=partner_group,
            contract=contract,
        )


@pytest.fixture
def ass_contract_context():
    group = PartnerGroup.objects.create(name="ASS Issue Groupe", slug="ass-issue")
    contributor = User.objects.create_user(
        username="ass-issue-apporteur",
        password="password",
        role=User.Role.CONTRIBUTOR,
        partner_group=group,
    )
    client = Client.objects.create(
        partner_group=group,
        contributor=contributor,
        created_by=contributor,
        first_name="Awa",
        last_name="Ndiaye",
        email="awa@example.test",
        phone="771112233",
    )
    vehicle = Vehicle.objects.create(
        partner_group=group,
        client=client,
        contributor=contributor,
        created_by=contributor,
        registration_number="DK-ASS-001",
        brand="Toyota",
        model="Yaris",
        chassis_number="CHASSIS-001",
        genre="VP",
        energy=Vehicle.Energy.GASOLINE,
        fiscal_power=8,
        seats=5,
        new_value=Decimal("9000000.00"),
        current_value=Decimal("3500000.00"),
    )
    quote = Quote.objects.create(
        partner_group=group,
        client=client,
        vehicle=vehicle,
        contributor=contributor,
        created_by=contributor,
        duration=12,
        periodicity=Quote.Periodicity.MONTHS,
        coverage_options=[1, 2, 4],
        civil_liability_amount=Decimal("18688.00"),
        premium_amount=Decimal("25000.00"),
        fees_amount=Decimal("3000.00"),
        total_amount=Decimal("28000.00"),
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
        external_reference="WAVE-TRX-001",
    )
    contract = Contract.objects.create(
        partner_group=group,
        quote=quote,
        payment=payment,
        client=client,
        vehicle=vehicle,
        contributor=contributor,
        created_by=contributor,
    )
    return {
        "group": group,
        "contributor": contributor,
        "client": client,
        "vehicle": vehicle,
        "quote": quote,
        "payment": payment,
        "contract": contract,
    }


@pytest.mark.django_db
def test_build_ass_qrcode_payload_uses_contract_data(ass_contract_context):
    payload = build_ass_qrcode_payload(ass_contract_context["contract"])

    assert payload["duree"] == 12
    assert payload["periodicite"] == Quote.Periodicity.MONTHS
    assert payload["typePersonne"] == "PHYSIQUE"
    assert payload["referenceTrxPartner"] == "WAVE-TRX-001"
    assert payload["responsabiliteCivile"] == 18688
    assert payload["garanties"] == [1, 2, 4]
    assert payload["assure"]["nom"] == "Ndiaye"
    assert payload["assure"]["prenom"] == "Awa"
    assert payload["vehicule"]["immatriculation"] == "DK-ASS-001"
    assert payload["vehicule"]["puissanceFiscale"] == 8


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("product_type", "method_name"),
    [
        (Quote.ProductType.AUTO, "request_qrcode"),
        (Quote.ProductType.MOTO, "request_moto_qrcode"),
        (Quote.ProductType.FLEET, "request_fleet_qrcode"),
        (Quote.ProductType.TRAILER, "request_trailer_qrcode"),
        (Quote.ProductType.GARAGE, "request_garage_qrcode"),
    ],
)
def test_ass_contract_issuer_routes_qrcode_by_product_type(
    ass_contract_context,
    product_type,
    method_name,
):
    Quote.objects.filter(pk=ass_contract_context["quote"].pk).update(
        product_type=product_type
    )
    ass_contract_context["contract"].refresh_from_db()
    ass_client = RecordingASSClient()
    issuer = ASSContractIssuer(client=ass_client)

    response = issuer.issue(ass_contract_context["contract"])

    assert response["contractNumber"] == "ASS-CONTRACT-123"
    assert ass_client.calls[0]["method"] == method_name
    assert ass_client.calls[0]["partner_group"] == ass_contract_context["group"]
    assert ass_client.calls[0]["contract"] == ass_contract_context["contract"]


@pytest.mark.django_db
def test_build_ass_qrcode_payload_for_fleet_wraps_single_contract_item(
    ass_contract_context,
):
    Quote.objects.filter(pk=ass_contract_context["quote"].pk).update(
        product_type=Quote.ProductType.FLEET
    )
    ass_contract_context["contract"].refresh_from_db()

    payload = build_ass_qrcode_payload_for_product(ass_contract_context["contract"])

    assert payload["referenceFlotte"].startswith("HORUS-FLEET-")
    assert payload["items"][0]["referenceTrxPartner"] == "WAVE-TRX-001"
    assert payload["items"][0]["responsabiliteCivile"] == 18688
    assert payload["items"][0]["vehicule"]["immatriculation"] == "DK-ASS-001"


@pytest.mark.django_db
def test_issue_contract_updates_references_from_ass_response(ass_contract_context):
    issuer = FakeIssuer()

    contract = issue_contract(
        contract=ass_contract_context["contract"],
        issuer=issuer,
    )

    assert issuer.calls == [ass_contract_context["contract"].id]
    assert contract.status == Contract.Status.ISSUED
    assert contract.contract_number == "ASS-CONTRACT-123"
    assert contract.attestation_reference == "ASS-ATT-123"
    assert contract.qr_code_reference == "ASS-QR-123"
    assert contract.issued_at is not None


@pytest.mark.django_db
def test_issue_contract_extracts_diotali_links_from_ass_response(ass_contract_context):
    issuer = FakeIssuer(
        response={
            "police": "ASS-CONTRACT-DIOTALI",
            "links": {
                "attestationUrl": "https://diotali.example.test/attestation.pdf",
                "qrCodeUrl": "https://diotali.example.test/qrcode.png",
            },
        }
    )

    contract = issue_contract(
        contract=ass_contract_context["contract"],
        issuer=issuer,
    )

    assert contract.contract_number == "ASS-CONTRACT-DIOTALI"
    assert contract.attestation_reference == "https://diotali.example.test/attestation.pdf"
    assert contract.qr_code_reference == "https://diotali.example.test/qrcode.png"


@pytest.mark.django_db
def test_issue_contract_does_not_call_ass_when_already_issued(ass_contract_context):
    Contract.objects.filter(pk=ass_contract_context["contract"].pk).update(
        status=Contract.Status.ISSUED,
        contract_number="ASS-CONTRACT-EXISTING",
        attestation_reference="ASS-ATT-EXISTING",
        qr_code_reference="ASS-QR-EXISTING",
    )
    ass_contract_context["contract"].refresh_from_db()
    issuer = FakeIssuer(exception=RuntimeError("ASS should not be called"))

    contract = issue_contract(
        contract=ass_contract_context["contract"],
        issuer=issuer,
    )

    assert issuer.calls == []
    assert contract.contract_number == "ASS-CONTRACT-EXISTING"


@pytest.mark.django_db
def test_issue_contract_blocks_unconfirmed_payment_before_ass_call(ass_contract_context):
    Payment.objects.filter(pk=ass_contract_context["payment"].pk).update(
        status=Payment.Status.PENDING,
        confirmed_at=None,
    )
    issuer = FakeIssuer()

    with pytest.raises(serializers.ValidationError):
        issue_contract(
            contract=ass_contract_context["contract"],
            issuer=issuer,
        )

    ass_contract_context["contract"].refresh_from_db()
    assert issuer.calls == []
    assert ass_contract_context["contract"].status == Contract.Status.READY_TO_ISSUE
    assert ass_contract_context["contract"].contract_number is None


@pytest.mark.django_db
def test_ass_exception_does_not_mark_contract_as_issued(ass_contract_context):
    issuer = FakeIssuer(exception=RuntimeError("ASS unavailable"))

    with pytest.raises(RuntimeError):
        issue_contract(
            contract=ass_contract_context["contract"],
            issuer=issuer,
        )

    ass_contract_context["contract"].refresh_from_db()
    assert issuer.calls == [ass_contract_context["contract"].id]
    assert ass_contract_context["contract"].status == Contract.Status.READY_TO_ISSUE
    assert ass_contract_context["contract"].contract_number is None
    assert ass_contract_context["contract"].attestation_reference is None
    assert ass_contract_context["contract"].qr_code_reference is None


@pytest.mark.django_db
def test_empty_ass_response_does_not_mark_contract_as_issued(ass_contract_context):
    issuer = FakeIssuer(response={"ok": True})

    with pytest.raises(serializers.ValidationError):
        issue_contract(
            contract=ass_contract_context["contract"],
            issuer=issuer,
        )

    ass_contract_context["contract"].refresh_from_db()
    assert issuer.calls == [ass_contract_context["contract"].id]
    assert ass_contract_context["contract"].status == Contract.Status.READY_TO_ISSUE
    assert ass_contract_context["contract"].contract_number is None
