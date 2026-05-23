from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from apps.ass_api.client import ASSAPIClient
from apps.audit.models import AuditLog
from apps.audit.services import record_audit_event
from apps.notifications.models import Notification
from apps.notifications.services import create_notifications_for_group
from apps.payments.models import Payment

from .ass_payloads import build_ass_qrcode_payload_for_product
from .models import Contract


QRCODE_METHOD_BY_PRODUCT_TYPE = {
    "AUTO": "request_qrcode",
    "MOTO": "request_moto_qrcode",
    "FLEET": "request_fleet_qrcode",
    "TRAILER": "request_trailer_qrcode",
    "GARAGE": "request_garage_qrcode",
}

QRCODE_ENDPOINT_BY_PRODUCT_TYPE = {
    "AUTO": "/api/v1/partner/qrcode.request",
    "MOTO": "/api/v1/partner/moto.request",
    "FLEET": "/api/v1/partner/qrcode.flotte.request",
    "TRAILER": "/api/v1/partner/remorque.qrcode.request",
    "GARAGE": "/api/v1/partner/garage.request",
}


class ASSContractIssuer:
    def __init__(self, client=None):
        self.client = client or ASSAPIClient()

    def issue(self, contract):
        payload = build_ass_qrcode_payload_for_product(contract)
        method_name = QRCODE_METHOD_BY_PRODUCT_TYPE.get(
            contract.quote.product_type,
            "request_qrcode",
        )
        request_method = getattr(self.client, method_name)
        return request_method(
            payload,
            partner_group=contract.partner_group,
            contract=contract,
        )


@transaction.atomic
def create_contract_from_payment(*, payment, created_by=None):
    payment = (
        Payment.objects.select_for_update()
        .select_related("partner_group", "quote", "client", "contributor")
        .get(pk=payment.pk)
    )

    if payment.status != Payment.Status.CONFIRMED:
        raise serializers.ValidationError(
            {"payment": "Aucun contrat ne peut etre cree sans paiement confirme."}
        )

    existing_contract = Contract.objects.filter(quote=payment.quote).first()
    if existing_contract:
        return existing_contract

    contract = Contract(
        partner_group=payment.partner_group,
        quote=payment.quote,
        payment=payment,
        client=payment.client,
        vehicle=payment.quote.vehicle,
        contributor=payment.contributor,
        created_by=created_by,
        status=Contract.Status.READY_TO_ISSUE,
    )
    contract.full_clean()
    contract.save()
    return contract


def issue_contract(*, contract, issuer=None, actor=None):
    contract = _get_issueable_contract(contract.pk)

    if contract.status == Contract.Status.ISSUED:
        return contract

    issuer = issuer or ASSContractIssuer()
    ass_response = issuer.issue(contract)

    with transaction.atomic():
        contract = (
            Contract.objects.select_for_update()
            .select_related("payment", "quote", "partner_group")
            .get(pk=contract.pk)
        )

        if contract.status == Contract.Status.ISSUED:
            return contract

        _validate_before_issue(contract)
        _apply_ass_response(contract, ass_response)
        contract.status = Contract.Status.ISSUED
        contract.issued_at = timezone.now()
        contract.full_clean()
        contract.save(
            update_fields=[
                "contract_number",
                "attestation_reference",
                "qr_code_reference",
                "attestation_url",
                "carte_brune_url",
                "status",
                "issued_at",
                "updated_at",
            ]
        )
        record_audit_event(
            action=AuditLog.Action.CONTRACT_ISSUED,
            partner_group=contract.partner_group,
            actor=actor,
            target=contract,
            metadata={
                "contract_number": contract.contract_number,
                "attestation_reference": contract.attestation_reference,
                "qr_code_reference": contract.qr_code_reference,
                "attestation_url": contract.attestation_url,
                "carte_brune_url": contract.carte_brune_url,
            },
        )
        create_notifications_for_group(
            partner_group=contract.partner_group,
            contributor=contract.contributor,
            notification_type=Notification.Type.CONTRACT_ISSUED,
            title="Contrat emis",
            message=f"Contrat {contract.contract_number} emis.",
            target=contract,
            metadata={
                "contract_id": contract.id,
                "contract_number": contract.contract_number,
                "attestation_reference": contract.attestation_reference,
                "qr_code_reference": contract.qr_code_reference,
                "attestation_url": contract.attestation_url,
                "carte_brune_url": contract.carte_brune_url,
            },
        )
        return contract


def build_contract_ass_payload_preview(*, contract):
    product_type = contract.quote.product_type
    return {
        "preview_only": True,
        "operation": "qrcode_issue",
        "product_type": product_type,
        "ass_method": QRCODE_METHOD_BY_PRODUCT_TYPE.get(
            product_type,
            "request_qrcode",
        ),
        "ass_endpoint": QRCODE_ENDPOINT_BY_PRODUCT_TYPE.get(
            product_type,
            "/api/v1/partner/qrcode.request",
        ),
        "payload": build_ass_qrcode_payload_for_product(contract),
    }


def _get_issueable_contract(contract_id):
    with transaction.atomic():
        contract = (
            Contract.objects.select_for_update()
            .select_related(
                "payment",
                "quote",
                "partner_group",
                "client",
                "vehicle",
                "contributor",
            )
            .get(pk=contract_id)
        )
        if contract.status != Contract.Status.ISSUED:
            _validate_before_issue(contract)
        return contract


def _validate_before_issue(contract):
    if contract.payment.status != Payment.Status.CONFIRMED:
        raise serializers.ValidationError(
            {"payment": "Aucune attestation ne peut etre generee sans paiement confirme."}
        )

    if contract.status == Contract.Status.CANCELLED:
        raise serializers.ValidationError(
            {"status": "Un contrat annule ne peut pas etre emis."}
        )


def _apply_ass_response(contract, ass_response):
    contract_number = _find_value(
        ass_response,
        ("contract_number", "contractNumber", "numeroPolice", "numero_police", "police"),
    )
    attestation_reference = _find_value(
        ass_response,
        (
            "attestation_reference",
            "attestationReference",
            "attestationNumber",
            "numeroAttestation",
            "referenceAttestation",
            "reference_attestation",
            "attestation",
        ),
    )
    qr_code_reference = _find_value(
        ass_response,
        (
            "qr_code_reference",
            "qrCodeReference",
            "qrcode_reference",
            "qrcode",
            "qrCode",
            "codeQr",
            "code_qr",
        ),
    )
    attestation_url = _find_value(
        ass_response,
        (
            "attestationUrl",
            "attestation_url",
            "attestationLink",
            "attestation_link",
            "linkAttestation",
            "link_attestation",
            "urlAttestation",
            "lienAttestation",
            "lienAttestationPdf",
            "attestationPdfUrl",
            "documentUrl",
            "policeUrl",
            "urlPolice",
            "lienPolice",
        ),
    )
    carte_brune_url = _find_value(
        ass_response,
        (
            "carteBruneUrl",
            "carte_brune_url",
            "carteBruneLink",
            "carte_brune_link",
            "linkCarteBrune",
            "link_carte_brune",
            "urlCarteBrune",
            "lienCarteBrune",
            "lienCarteBrunePdf",
            "carteBrunePdfUrl",
            "carteBrune",
            "carte_brune",
            "brownCardUrl",
            "brown_card_url",
            "brownCardLink",
        ),
    )

    if not any(
        (
            contract_number,
            attestation_reference,
            qr_code_reference,
            attestation_url,
            carte_brune_url,
        )
    ):
        raise serializers.ValidationError(
            {"ass_api": "La reponse ASS ne contient aucune reference exploitable."}
        )

    if contract_number:
        contract.contract_number = str(contract_number)
    if attestation_reference:
        contract.attestation_reference = str(attestation_reference)
    if qr_code_reference:
        contract.qr_code_reference = str(qr_code_reference)
    if attestation_url:
        contract.attestation_url = str(attestation_url)
    if carte_brune_url:
        contract.carte_brune_url = str(carte_brune_url)


def _find_value(value, keys):
    normalized_keys = {_normalize_key(key) for key in keys}

    if isinstance(value, dict):
        for key, nested_value in value.items():
            if _normalize_key(key) in normalized_keys and nested_value not in (None, ""):
                return nested_value
        for nested_value in value.values():
            found_value = _find_value(nested_value, keys)
            if found_value not in (None, ""):
                return found_value

    if isinstance(value, list):
        for item in value:
            found_value = _find_value(item, keys)
            if found_value not in (None, ""):
                return found_value

    return None


def _normalize_key(key):
    return str(key).strip().replace("_", "").replace("-", "").replace(" ", "").lower()
