from apps.reference_data.services import quote_product_code

from .trailers import (
    trailer_reference_contract_id_value,
    trailer_reference_vehicle_contract,
    trailer_reference_vehicle_value,
)


def build_contract_document_items(contract, *, include_urls=True):
    return build_quote_expected_document_items(
        quote=contract.quote,
        contract=contract,
        include_urls=include_urls,
    )


def build_quote_expected_document_items(*, quote, contract=None, include_urls=False):
    if quote_product_code(quote) == "TRAILER":
        reference_contract = trailer_reference_vehicle_contract(quote)
        return [
            _document_item(
                code="TRACTOR_ATTESTATION",
                label="Attestation vehicule tracteur",
                vehicle_role="tractor",
                document_kind="attestation",
                source_contract=reference_contract,
                url_field="attestation_url",
                include_urls=include_urls,
            ),
            _document_item(
                code="TRACTOR_CARTE_BRUNE",
                label="Carte brune CEDEAO vehicule tracteur",
                vehicle_role="tractor",
                document_kind="carte_brune",
                source_contract=reference_contract,
                url_field="carte_brune_url",
                include_urls=include_urls,
            ),
            _document_item(
                code="TRAILER_ATTESTATION",
                label="Attestation remorque",
                vehicle_role="trailer",
                document_kind="attestation",
                source_contract=contract,
                url_field="attestation_url",
                include_urls=include_urls,
            ),
            _document_item(
                code="TRAILER_CARTE_BRUNE",
                label="Carte brune CEDEAO remorque",
                vehicle_role="trailer",
                document_kind="carte_brune",
                source_contract=contract,
                url_field="carte_brune_url",
                include_urls=include_urls,
            ),
        ]

    return [
        _document_item(
            code="ATTESTATION",
            label="Attestation",
            vehicle_role="insured_vehicle",
            document_kind="attestation",
            source_contract=contract,
            url_field="attestation_url",
            include_urls=include_urls,
        ),
        _document_item(
            code="CARTE_BRUNE",
            label="Carte brune CEDEAO",
            vehicle_role="insured_vehicle",
            document_kind="carte_brune",
            source_contract=contract,
            url_field="carte_brune_url",
            include_urls=include_urls,
        ),
    ]


def build_trailer_documents_summary(contract):
    if quote_product_code(contract.quote) != "TRAILER":
        return {
            "applies": False,
            "requires_four_documents": False,
            "reference_vehicle": "",
            "reference_vehicle_contract_id": None,
            "reference_vehicle_contract": None,
            "complete": False,
        }

    reference_contract = trailer_reference_vehicle_contract(contract.quote)
    documents = build_contract_document_items(contract, include_urls=False)
    return {
        "applies": True,
        "requires_four_documents": True,
        "reference_vehicle": trailer_reference_vehicle_value(contract.quote),
        "reference_vehicle_contract_id": trailer_reference_contract_id_value(
            contract.quote
        ),
        "reference_vehicle_contract": _contract_summary(reference_contract),
        "complete": all(document["available"] for document in documents),
    }


def _document_item(
    *,
    code,
    label,
    vehicle_role,
    document_kind,
    source_contract,
    url_field,
    include_urls,
):
    url = getattr(source_contract, url_field, "") if source_contract else ""
    item = {
        "code": code,
        "label": label,
        "vehicle_role": vehicle_role,
        "document_kind": document_kind,
        "required_after_issue": True,
        "available": bool(url),
        "contract_id": source_contract.id if source_contract else None,
        "contract_number": (
            source_contract.contract_number if source_contract else ""
        ),
        "attestation_reference": (
            source_contract.attestation_reference if source_contract else ""
        ),
    }
    if include_urls:
        item["url"] = url
    return item


def _contract_summary(contract):
    if contract is None:
        return None
    return {
        "id": contract.id,
        "status": contract.status,
        "contract_number": contract.contract_number,
        "attestation_reference": contract.attestation_reference,
        "vehicle_registration_number": contract.vehicle.registration_number,
    }
