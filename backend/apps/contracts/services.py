import httpx
from datetime import datetime, timedelta
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from apps.ass_api.applicationtiers import (
    ApplicationTiersPublicClient,
    get_applicationtiers_public_endpoints,
)
from apps.ass_api.client import ASSAPIClient
from apps.audit.models import AuditLog
from apps.audit.services import record_audit_event
from apps.notifications.models import Notification
from apps.notifications.services import (
    create_client_notification,
    create_notifications_for_group,
)
from apps.payments.models import Payment
from apps.reference_data.services import quote_product_code

from .ass_payloads import build_ass_qrcode_payload_for_product
from .documents import build_contract_document_items, build_trailer_documents_summary
from .models import Contract
from .trailers import trailer_reference_vehicle_value


QRCODE_METHOD_BY_PRODUCT_TYPE = {
    "AUTO": "request_qrcode",
    "MOTO": "request_moto_qrcode",
    "FLEET": "request_fleet_qrcode",
    "TRAILER": "request_trailer_qrcode",
    "SCHOOL_BUS": "request_school_bus_qrcode",
    "GARAGE": "request_garage_qrcode",
}

QRCODE_ENDPOINT_BY_PRODUCT_TYPE = {
    "AUTO": "/api/v1/partner/qrcode.request",
    "MOTO": "/api/v1/partner/moto.request",
    "FLEET": "/api/v1/partner/qrcode.flotte.request",
    "TRAILER": "/api/v1/partner/remorque.qrcode.request",
    "SCHOOL_BUS": "/api/v1/partner/bus.ecole.request",
    "GARAGE": "/api/v1/partner/garage.request",
}


class DiotaliPublicVerificationBlocked(Exception):
    def __init__(self, verification):
        self.verification = verification
        super().__init__(verification.get("correction_message") or "Emission bloquee.")


class ASSContractIssuer:
    def __init__(self, client=None):
        self.client = client or ASSAPIClient()

    def issue(self, contract):
        payload = build_ass_qrcode_payload_for_product(contract)
        product_code = quote_product_code(contract.quote)
        method_name = QRCODE_METHOD_BY_PRODUCT_TYPE.get(
            product_code,
            "request_qrcode",
        )
        request_method = getattr(self.client, method_name)
        return request_method(
            payload,
            partner_group=contract.partner_group,
            contract=contract,
        )


def build_contract_issue_readiness(*, contract):
    product_type = quote_product_code(contract.quote)
    checks = [
        _check(
            "contract_status",
            contract.status == Contract.Status.READY_TO_ISSUE,
            "Le contrat est pret a etre emis.",
            f"Le contrat doit etre {Contract.Status.READY_TO_ISSUE}.",
        ),
        _check(
            "payment_confirmed",
            contract.payment.status == Payment.Status.CONFIRMED,
            "Le paiement est confirme.",
            "Le paiement doit etre confirme.",
        ),
        _check(
            "payment_amount_matches_quote",
            contract.payment.amount == contract.quote.total_amount,
            "Le montant paye correspond au total du devis.",
            "Le montant paye doit correspondre au total du devis.",
        ),
        _check(
            "contract_relations",
            _contract_relations_are_consistent(contract),
            "Le contrat, le devis, le paiement, le client et le vehicule sont coherents.",
            "Le contrat doit utiliser le devis, le paiement, le client et le vehicule rattaches.",
        ),
        _check(
            "supported_product",
            product_type in QRCODE_METHOD_BY_PRODUCT_TYPE,
            "Le produit est supporte pour Diotali.",
            "Le produit n'est pas supporte pour l'emission Diotali.",
        ),
    ]
    if product_type == "TRAILER":
        checks.append(
            _check(
                "trailer_reference_vehicle",
                bool(trailer_reference_vehicle_value(contract.quote)),
                "La referenceExterne du vehicule tracteur est presente.",
                (
                    "referenceVehicule est obligatoire pour emettre une remorque. "
                    "L'utilisateur doit renseigner la referenceExterne du contrat "
                    "AUTO tracteur ou abandonner l'emission."
                ),
            )
        )
    payload = None
    payload_error = ""
    try:
        payload = build_ass_qrcode_payload_for_product(contract)
    except serializers.ValidationError as exc:
        payload_error = exc.detail
    checks.append(
        _check(
            "payload_build",
            payload is not None,
            "Le payload Diotali local est constructible.",
            "Le payload Diotali local est incomplet ou invalide.",
            detail=payload_error,
        )
    )
    if payload is not None:
        checks.append(
            _check(
                "payload_reference",
                bool(_find_value(payload, ("referenceTrxPartner", "reference_trx_partner"))),
                "La reference transaction partenaire est presente.",
                "La reference transaction partenaire est obligatoire.",
            )
        )
        checks.append(
            _check(
                "payload_policy",
                bool(_find_value(payload, ("police", "contractNumber", "numeroPolice"))),
                "La reference police locale est presente.",
                "La reference police locale est obligatoire.",
            )
        )

    return {
        "ready": all(check["passed"] for check in checks),
        "operation": "diotali_issue_readiness",
        "product_type": product_type,
        "ass_method": QRCODE_METHOD_BY_PRODUCT_TYPE.get(product_type),
        "ass_endpoint": QRCODE_ENDPOINT_BY_PRODUCT_TYPE.get(product_type),
        "checks": checks,
        "payload": payload,
        "expected_response_fields": {
            "contract": [
                "contractNumber",
                "police",
                "numeroPolice",
                "referenceExterne",
            ],
            "attestation": [
                "attestationNumber",
                "attestationReference",
                "linkAttestation",
                "attestationUrl",
            ],
            "carte_brune": [
                "linkCarteBrune",
                "carteBruneUrl",
            ],
        },
        "expected_documents": build_contract_document_items(
            contract,
            include_urls=False,
        ),
        "trailer_documents": build_trailer_documents_summary(contract),
        "public_vehicle_verification": {
            "status": "not_run",
            "endpoint": "diotali-verification",
            "required_for_issue": getattr(
                settings,
                "AAS_PUBLIC_VERIFY_BEFORE_ISSUE",
                True,
            ),
            "public_endpoints": get_applicationtiers_public_endpoints(),
        },
    }


def validate_contract_issue_readiness(*, contract):
    readiness = build_contract_issue_readiness(contract=contract)
    if readiness["ready"]:
        return readiness
    raise serializers.ValidationError(
        {
            "issue_readiness": [
                check
                for check in readiness["checks"]
                if not check["passed"]
            ]
        }
    )


def verify_contract_vehicle_on_diotali_public(*, contract, client=None):
    public_client = client or ApplicationTiersPublicClient()
    registration_number = contract.vehicle.registration_number
    try:
        result = public_client.verify_vehicle(registration_number)
    except ValueError as exc:
        raise serializers.ValidationError({"diotali_public": str(exc)}) from exc
    except httpx.HTTPError as exc:
        raise serializers.ValidationError(
            {"diotali_public": "La verification publique Diotali a echoue."}
        ) from exc

    return {
        "operation": "diotali_public_vehicle_verification",
        "registration_number": registration_number,
        "normalized_registration_number": public_client.normalize_immat(
            registration_number
        ),
        "public_endpoints": public_client.get_public_endpoints(),
        "verification": _applicationtiers_verification_summary(
            result,
            quote_effective_date=contract.quote.effective_date,
        ),
        "result": result,
    }


def validate_public_vehicle_not_already_insured(*, contract, client=None):
    if not getattr(settings, "AAS_PUBLIC_VERIFY_BEFORE_ISSUE", True):
        return None

    verification_payload = verify_contract_vehicle_on_diotali_public(
        contract=contract,
        client=client,
    )
    verification = verification_payload["verification"]
    if verification["blocks_issue"]:
        raise DiotaliPublicVerificationBlocked(verification)
    return verification_payload


@transaction.atomic
def create_contract_from_payment(*, payment, created_by=None):
    payment = (
        Payment.objects.select_for_update()
        .select_related(
            "partner_group",
            "quote",
            "quote__product_reference",
            "quote__duration_option",
            "quote__vehicle",
            "quote__vehicle__brand_reference",
            "quote__vehicle__genre_reference",
            "quote__vehicle__energy_reference",
            "client",
            "contributor",
        )
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

    validate_public_vehicle_not_already_insured(contract=contract)
    issuer = issuer or ASSContractIssuer()
    ass_response = issuer.issue(contract)

    with transaction.atomic():
        contract = (
            Contract.objects.select_for_update()
            .select_related(
                "payment",
                "quote",
                "quote__product_reference",
                "quote__duration_option",
                "partner_group",
            )
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
        create_client_notification(
            partner_group=contract.partner_group,
            client=contract.client,
            notification_type=Notification.Type.CONTRACT_ISSUED,
            title="Contrat emis",
            message=f"Votre contrat {contract.contract_number} est disponible.",
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
    product_type = quote_product_code(contract.quote)
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


def _check(code, passed, success_message, failure_message, *, detail=""):
    return {
        "code": code,
        "passed": bool(passed),
        "message": success_message if passed else failure_message,
        "detail": detail,
    }


def _contract_relations_are_consistent(contract):
    return (
        contract.quote.partner_group_id == contract.partner_group_id
        and contract.payment.partner_group_id == contract.partner_group_id
        and contract.client.partner_group_id == contract.partner_group_id
        and contract.vehicle.partner_group_id == contract.partner_group_id
        and contract.payment.quote_id == contract.quote_id
        and contract.payment.client_id == contract.client_id
        and contract.quote.client_id == contract.client_id
        and contract.quote.vehicle_id == contract.vehicle_id
    )


def _applicationtiers_verification_summary(result, *, quote_effective_date=None):
    if not isinstance(result, dict):
        return {
            "is_valid": False,
            "status": "UNKNOWN",
            "blocks_issue": False,
            "overlaps_requested_effective_date": False,
            "message": "Reponse ApplicationTiers inattendue.",
            "attestation_number": "",
            "registration_number": "",
            "effective_date": "",
            "expiration_date": "",
            "verification_date": "",
            "brand": "",
            "model": "",
            "current_quote_effective_date": _date_or_empty(quote_effective_date),
            "suggested_effective_date": "",
            "correction_message": "",
        }

    data = result.get("data") if isinstance(result.get("data"), dict) else {}
    status = str(result.get("operationStatus") or "").strip().upper()
    is_valid = status == "SUCCESS"
    expiration_date = data.get("dateEcheance") or ""
    suggested_effective_date = _suggest_next_effective_date(expiration_date)
    overlaps_requested_effective_date = _overlaps_requested_effective_date(
        expiration_date=expiration_date,
        quote_effective_date=quote_effective_date,
    )
    blocks_issue = is_valid and overlaps_requested_effective_date
    attestation_number = data.get("attestationNumber") or ""
    registration_number = (
        data.get("immatriculation") or result.get("queriedImmatriculation") or ""
    )
    return {
        "is_valid": is_valid,
        "status": status or "UNKNOWN",
        "blocks_issue": blocks_issue,
        "overlaps_requested_effective_date": overlaps_requested_effective_date,
        "message": result.get("operationMessage") or "",
        "attestation_number": attestation_number,
        "registration_number": registration_number,
        "effective_date": data.get("dateEffet") or "",
        "expiration_date": expiration_date,
        "verification_date": data.get("dateVerification") or "",
        "brand": data.get("marque") or "",
        "model": data.get("modele") or "",
        "current_quote_effective_date": _date_or_empty(quote_effective_date),
        "suggested_effective_date": suggested_effective_date,
        "correction_message": _applicationtiers_correction_message(
            blocks_issue=blocks_issue,
            attestation_number=attestation_number,
            registration_number=registration_number,
            expiration_date=expiration_date,
            suggested_effective_date=suggested_effective_date,
        ),
    }


def _overlaps_requested_effective_date(*, expiration_date, quote_effective_date):
    if not expiration_date:
        return True
    if quote_effective_date is None:
        return True
    parsed_expiration_date = _parse_applicationtiers_date(expiration_date)
    if parsed_expiration_date is None:
        return True
    return quote_effective_date <= parsed_expiration_date


def _applicationtiers_correction_message(
    *,
    blocks_issue,
    attestation_number,
    registration_number,
    expiration_date,
    suggested_effective_date,
):
    if not blocks_issue:
        return ""
    message = "Une attestation Diotali est deja valide pour cette immatriculation."
    if attestation_number:
        message += f" Attestation existante : {attestation_number}."
    if registration_number:
        message += f" Immatriculation : {registration_number}."
    if expiration_date:
        message += f" Echeance actuelle : {expiration_date}."
    if suggested_effective_date:
        message += (
            " L'utilisateur doit corriger la date d'effet du devis a partir du "
            f"{suggested_effective_date}, ou abandonner l'emission."
        )
    else:
        message += (
            " L'utilisateur doit corriger la date d'effet du devis apres "
            "l'echeance actuelle, ou abandonner l'emission."
        )
    return message


def _suggest_next_effective_date(expiration_date):
    parsed_expiration_date = _parse_applicationtiers_date(expiration_date)
    if parsed_expiration_date is None:
        return ""
    return (parsed_expiration_date + timedelta(days=1)).isoformat()


def _parse_applicationtiers_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(str(value).strip()[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def _date_or_empty(value):
    if value is None:
        return ""
    return value.isoformat()


def _get_issueable_contract(contract_id):
    with transaction.atomic():
        contract = (
            Contract.objects.select_for_update()
            .select_related(
                "payment",
                "quote",
                "quote__product_reference",
                "quote__duration_option",
                "partner_group",
                "client",
                "vehicle",
                "vehicle__brand_reference",
                "vehicle__genre_reference",
                "vehicle__energy_reference",
                "contributor",
            )
            .get(pk=contract_id)
        )
        if contract.status != Contract.Status.ISSUED:
            validate_contract_issue_readiness(contract=contract)
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
        (
            "contract_number",
            "contractNumber",
            "numeroPolice",
            "numero_police",
            "police",
            "referenceExterne",
            "reference_externe",
            "externalReference",
            "external_reference",
        ),
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
