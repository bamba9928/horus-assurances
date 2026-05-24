import json
from io import StringIO
from pathlib import Path
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings
from rest_framework import serializers

from apps.ass_api.models import ASSAPICallLog
from apps.ass_api.sanitizers import REDACTED
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
FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"


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

    def request_school_bus_qrcode(self, payload, *, partner_group=None, contract=None):
        return self._record(
            "request_school_bus_qrcode",
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
    Quote.objects.filter(pk=ass_contract_context["quote"].pk).update(
        ass_product_data={
            "garantiesOptPT": "OPTION_1",
            "garantiesOptAR": "500000",
            "garantiesOptAS": "OPTION_1",
        }
    )
    ass_contract_context["contract"].refresh_from_db()

    payload = build_ass_qrcode_payload(ass_contract_context["contract"])

    assert payload["duree"] == 12
    assert payload["periodicite"] == Quote.Periodicity.MONTHS
    assert payload["typePersonne"] == "PHYSIQUE"
    assert payload["referenceTrxPartner"] == "WAVE-TRX-001"
    assert payload["responsabiliteCivile"] == 18688
    assert payload["garanties"] == [1, 2, 4]
    assert payload["garantiesOptPT"] == "OPTION_1"
    assert payload["garantiesOptAR"] == "500000"
    assert payload["garantiesOptAS"] == "OPTION_1"
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
        (Quote.ProductType.SCHOOL_BUS, "request_school_bus_qrcode"),
        (Quote.ProductType.GARAGE, "request_garage_qrcode"),
    ],
)
def test_ass_contract_issuer_routes_qrcode_by_product_type(
    ass_contract_context,
    product_type,
    method_name,
):
    ass_product_data = {}
    if product_type == Quote.ProductType.MOTO:
        ass_product_data = {"cylindre": 126, "usage": "NON_COMMERCIAL"}
    if product_type == Quote.ProductType.TRAILER:
        ass_product_data = {"referenceVehicule": "DK-TRACT-001"}
    if product_type == Quote.ProductType.GARAGE:
        ass_product_data = {"nombreCarte": 2}

    Quote.objects.filter(pk=ass_contract_context["quote"].pk).update(
        product_type=product_type,
        ass_product_data=ass_product_data,
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
def test_build_ass_qrcode_payload_for_moto_uses_product_data(ass_contract_context):
    Quote.objects.filter(pk=ass_contract_context["quote"].pk).update(
        product_type=Quote.ProductType.MOTO,
        ass_product_data={"cylindre": 126, "usage": "NON_COMMERCIAL"},
    )
    ass_contract_context["contract"].refresh_from_db()

    payload = build_ass_qrcode_payload_for_product(ass_contract_context["contract"])

    assert payload["vehicule"]["cylindre"] == 126
    assert payload["vehicule"]["usage"] == "NON_COMMERCIAL"
    assert payload["garanties"] == [1, 2, 4]


@pytest.mark.django_db
def test_build_ass_qrcode_payload_for_trailer_uses_product_reference(
    ass_contract_context,
):
    Quote.objects.filter(pk=ass_contract_context["quote"].pk).update(
        product_type=Quote.ProductType.TRAILER,
        ass_product_data={"referenceVehicule": "DK-TRACT-001"},
    )
    ass_contract_context["contract"].refresh_from_db()

    payload = build_ass_qrcode_payload_for_product(ass_contract_context["contract"])

    assert payload["referenceVehicule"] == "DK-TRACT-001"
    assert payload["immatriculation"] == "DK-ASS-001"


@pytest.mark.django_db
def test_build_ass_qrcode_payload_for_garage_uses_card_count(
    ass_contract_context,
):
    Quote.objects.filter(pk=ass_contract_context["quote"].pk).update(
        product_type=Quote.ProductType.GARAGE,
        ass_product_data={"nombreCarte": 2},
    )
    ass_contract_context["contract"].refresh_from_db()

    payload = build_ass_qrcode_payload_for_product(ass_contract_context["contract"])

    assert payload["nombreCarte"] == 2
    assert payload["genre"] == "VP"


@pytest.mark.django_db
def test_build_ass_qrcode_payload_for_school_bus_uses_vehicle_payload(
    ass_contract_context,
):
    Vehicle.objects.filter(pk=ass_contract_context["vehicle"].pk).update(
        registration_number="DK-BUS-001",
        brand="Mercedes",
        model="Bus",
        chassis_number="BUS-CHASSIS-001",
        genre="BE-VTA",
        fiscal_power=20,
        seats=30,
        new_value=Decimal("45000000.00"),
        current_value=Decimal("35000000.00"),
    )
    Quote.objects.filter(pk=ass_contract_context["quote"].pk).update(
        product_type=Quote.ProductType.SCHOOL_BUS,
        coverage_options=[],
    )
    ass_contract_context["contract"].refresh_from_db()

    payload = build_ass_qrcode_payload_for_product(ass_contract_context["contract"])

    assert payload["duree"] == 12
    assert payload["periodicite"] == Quote.Periodicity.MONTHS
    assert payload["cout_police"] == 3000
    assert payload["remise_rc"] == 0
    assert payload["responsabiliteCivile"] == 18688
    assert payload["garanties"] == []
    assert payload["vehicule"]["immatriculation"] == "DK-BUS-001"
    assert payload["vehicule"]["genre"] == "BE-VTA"
    assert payload["vehicule"]["nombrePlace"] == 30
    assert payload["vehicule"]["puissanceFiscale"] == 20


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
                "carteBruneUrl": "https://diotali.example.test/carte-brune.pdf",
            },
        }
    )

    contract = issue_contract(
        contract=ass_contract_context["contract"],
        issuer=issuer,
    )

    assert contract.contract_number == "ASS-CONTRACT-DIOTALI"
    assert contract.attestation_reference is None
    assert contract.qr_code_reference is None
    assert contract.attestation_url == "https://diotali.example.test/attestation.pdf"
    assert contract.carte_brune_url == "https://diotali.example.test/carte-brune.pdf"


@pytest.mark.django_db
def test_issue_contract_extracts_documented_diotali_link_keys(ass_contract_context):
    issuer = FakeIssuer(
        response={
            "data": {
                "referenceExterne": "WAVE-TRX-001",
                "attestationNumber": "SN00JTEST",
                "linkAttestation": "https://diotali.example.test/attestation/SN00JTEST",
                " linkCarteBrune ": "https://diotali.example.test/carte/SN00JTEST",
            },
        }
    )

    contract = issue_contract(
        contract=ass_contract_context["contract"],
        issuer=issuer,
    )

    assert contract.attestation_reference == "SN00JTEST"
    assert contract.attestation_url == "https://diotali.example.test/attestation/SN00JTEST"
    assert contract.carte_brune_url == "https://diotali.example.test/carte/SN00JTEST"


@pytest.mark.django_db
def test_issue_contract_matches_real_moto_qrcode_success_fixture(ass_contract_context):
    fixture = json.loads((FIXTURE_DIR / "ass_moto_qrcode_success.json").read_text())
    issuer = FakeIssuer(response=fixture["body"])

    contract = issue_contract(
        contract=ass_contract_context["contract"],
        issuer=issuer,
    )

    assert fixture["status_code"] == 200
    assert fixture["body"]["operationStatus"] == "SUCCESS"
    assert contract.attestation_reference == "SN004FTNNGK"
    assert contract.attestation_url == "https://aas.diotali.com/#/attestation/SN004FTNNGK"
    assert contract.carte_brune_url == "https://aas.diotali.com/#/carte-brune/SN004FTNNGK"
    assert contract.qr_code_reference is None


@pytest.mark.django_db
def test_issue_contract_matches_real_auto_qrcode_success_fixture(ass_contract_context):
    fixture = json.loads((FIXTURE_DIR / "ass_auto_qrcode_success.json").read_text())
    issuer = FakeIssuer(response=fixture["body"])

    contract = issue_contract(
        contract=ass_contract_context["contract"],
        issuer=issuer,
    )

    assert fixture["status_code"] == 201
    assert fixture["body"]["operationStatus"] == "SUCCESS"
    assert contract.attestation_reference == "SN004Q6BMD5"
    assert contract.attestation_url == "https://aas.diotali.com/#/attestation/SN004Q6BMD5"
    assert contract.carte_brune_url == "https://aas.diotali.com/#/carte-brune/SN004Q6BMD5"
    assert contract.qr_code_reference is None


@pytest.mark.django_db
def test_issue_contract_matches_real_trailer_qrcode_success_fixture(
    ass_contract_context,
):
    fixture = json.loads((FIXTURE_DIR / "ass_trailer_qrcode_success.json").read_text())
    issuer = FakeIssuer(response=fixture["body"])

    contract = issue_contract(
        contract=ass_contract_context["contract"],
        issuer=issuer,
    )

    assert fixture["status_code"] == 201
    assert fixture["body"]["operationStatus"] == "SUCCESS"
    assert contract.attestation_reference == "SN004NFKDEI"
    assert contract.attestation_url == "https://aas.diotali.com/#/attestation/SN004NFKDEI"
    assert contract.carte_brune_url == "https://aas.diotali.com/#/carte-brune/SN004NFKDEI"
    assert contract.qr_code_reference is None


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


@pytest.mark.django_db
def test_validate_ass_sandbox_issue_command_previews_without_external_call(
    ass_contract_context,
    monkeypatch,
):
    class FailingCommandIssuer:
        def issue(self, contract):
            raise AssertionError("external ASS call should not be made")

    monkeypatch.setattr(
        "apps.contracts.management.commands.validate_ass_sandbox_issue.ASSContractIssuer",
        FailingCommandIssuer,
    )
    output = StringIO()

    call_command(
        "validate_ass_sandbox_issue",
        ass_contract_context["contract"].id,
        stdout=output,
    )

    command_output = output.getvalue()
    assert "ass_payload_preview" in command_output
    assert "/api/v1/partner/qrcode.request" in command_output
    assert "Aucun appel externe ASS effectue" in command_output


@pytest.mark.django_db
@override_settings(ASS_BASE_URL="https://manager.example.com")
def test_validate_ass_sandbox_issue_command_blocks_non_sandbox_url(
    ass_contract_context,
    monkeypatch,
):
    class FailingCommandIssuer:
        def issue(self, contract):
            raise AssertionError("external ASS call should not be made")

    monkeypatch.setattr(
        "apps.contracts.management.commands.validate_ass_sandbox_issue.ASSContractIssuer",
        FailingCommandIssuer,
    )

    with pytest.raises(CommandError, match="ne ressemble pas a une sandbox"):
        call_command(
            "validate_ass_sandbox_issue",
            ass_contract_context["contract"].id,
            "--confirm-external-ass-call",
            stdout=StringIO(),
        )


@pytest.mark.django_db
@override_settings(ASS_BASE_URL="https://kiiraytest.example.com")
def test_validate_ass_sandbox_issue_command_calls_ass_without_persisting(
    ass_contract_context,
    monkeypatch,
):
    class FakeCommandIssuer:
        calls = []

        def issue(self, contract):
            self.__class__.calls.append(contract.id)
            return {
                "contractNumber": "ASS-SANDBOX-001",
                "password": "response-password-secret",
                "operationStatus": "SUCCESS",
            }

    monkeypatch.setattr(
        "apps.contracts.management.commands.validate_ass_sandbox_issue.ASSContractIssuer",
        FakeCommandIssuer,
    )
    output = StringIO()

    call_command(
        "validate_ass_sandbox_issue",
        ass_contract_context["contract"].id,
        "--confirm-external-ass-call",
        stdout=output,
    )

    ass_contract_context["contract"].refresh_from_db()
    command_output = output.getvalue()
    assert FakeCommandIssuer.calls == [ass_contract_context["contract"].id]
    assert "ASS-SANDBOX-001" in command_output
    assert "response-password-secret" not in command_output
    assert REDACTED in command_output
    assert '"persisted_contract_issue": false' in command_output
    assert ass_contract_context["contract"].status == Contract.Status.READY_TO_ISSUE
    assert ass_contract_context["contract"].contract_number is None


@pytest.mark.django_db
@override_settings(ASS_BASE_URL="https://kiiraytest.example.com")
def test_validate_ass_sandbox_issue_command_reports_business_error_cleanly(
    ass_contract_context,
    monkeypatch,
):
    class FakeCommandIssuer:
        def issue(self, contract):
            ASSAPICallLog.objects.create(
                partner_group=contract.partner_group,
                contract=contract,
                endpoint="/api/v1/partner/moto.request",
                method="POST",
                status=ASSAPICallLog.Status.ERROR,
                http_status_code=200,
                request_payload={"password": "request-secret"},
                response_payload={
                    "operationStatus": "ERROR",
                    "operationMessage": "Mot de passe password=response-secret",
                },
                error_message="password=response-secret",
            )
            raise serializers.ValidationError(
                {"ass_api": "Mot de passe password=response-secret"}
            )

    monkeypatch.setattr(
        "apps.contracts.management.commands.validate_ass_sandbox_issue.ASSContractIssuer",
        FakeCommandIssuer,
    )
    output = StringIO()

    with pytest.raises(CommandError, match="Appel ASS echoue"):
        call_command(
            "validate_ass_sandbox_issue",
            ass_contract_context["contract"].id,
            "--confirm-external-ass-call",
            stdout=output,
        )

    command_output = output.getvalue()
    assert "ass_error" in command_output
    assert "/api/v1/partner/moto.request" in command_output
    assert "response-secret" not in command_output
    assert REDACTED in command_output
