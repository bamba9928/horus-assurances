from rest_framework import serializers


TRAILER_REFERENCE_VEHICLE_KEYS = (
    "referenceVehicule",
    "reference_vehicule",
    "referenceVehicle",
    "reference_vehicle",
)

TRAILER_REFERENCE_CONTRACT_ID_KEYS = (
    "referenceVehicleContractId",
    "reference_vehicle_contract_id",
    "tractor_contract_id",
    "tracteur_contract_id",
    "vehicle_contract_id",
)


def trailer_reference_vehicle_value(quote):
    value = _raw_trailer_reference_vehicle_value(quote)
    if value:
        return value
    reference_contract = trailer_reference_vehicle_contract(quote)
    if reference_contract and reference_contract.contract_number:
        return reference_contract.contract_number
    return ""


def required_trailer_reference_vehicle_value(quote):
    value = trailer_reference_vehicle_value(quote)
    if value:
        return value
    raise serializers.ValidationError(
        {
            "ass_product_data": (
                "referenceVehicule est obligatoire pour une remorque. "
                "Utiliser la referenceExterne du contrat AUTO tracteur."
            )
        }
    )


def trailer_reference_vehicle_contract(quote):
    contract_id = _product_data_value(quote, *TRAILER_REFERENCE_CONTRACT_ID_KEYS)
    if contract_id not in (None, ""):
        contract = _find_contract_by_id(quote, contract_id)
        if contract is not None:
            return contract

    reference = _raw_trailer_reference_vehicle_value(quote)
    if not reference:
        return None
    from apps.contracts.models import Contract

    return (
        Contract.objects.select_related("quote", "vehicle", "client", "payment")
        .filter(
            partner_group_id=quote.partner_group_id,
            client_id=quote.client_id,
            status=Contract.Status.ISSUED,
            contract_number=reference,
        )
        .first()
    )


def trailer_reference_contract_id_value(quote):
    value = _product_data_value(quote, *TRAILER_REFERENCE_CONTRACT_ID_KEYS)
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _find_contract_by_id(quote, contract_id):
    normalized_contract_id = _normalize_contract_id(contract_id)
    if normalized_contract_id is None:
        return None
    from apps.contracts.models import Contract

    return (
        Contract.objects.select_related("quote", "vehicle", "client", "payment")
        .filter(
            id=normalized_contract_id,
            partner_group_id=quote.partner_group_id,
            client_id=quote.client_id,
            status=Contract.Status.ISSUED,
        )
        .exclude(contract_number__isnull=True)
        .exclude(contract_number="")
        .first()
    )


def _normalize_contract_id(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _raw_trailer_reference_vehicle_value(quote):
    return _product_data_value(quote, *TRAILER_REFERENCE_VEHICLE_KEYS, default="")


def _product_data_value(quote, *keys, default=None):
    data = quote.ass_product_data or {}
    if not isinstance(data, dict):
        raise serializers.ValidationError(
            {"ass_product_data": "Les donnees produit ASS doivent etre un objet JSON."}
        )
    for key in keys:
        value = data.get(key)
        if value not in (None, ""):
            return str(value).strip()
    return default
