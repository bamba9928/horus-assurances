from decimal import Decimal

from rest_framework import serializers


def build_ass_qrcode_payload(contract):
    quote = contract.quote
    client = contract.client
    vehicle = contract.vehicle

    payload = {
        "duree": quote.duration,
        "assure": _client_payload(client),
        "police": contract.contract_number or f"HORUS-PENDING-{contract.id:06d}",
        "vehicule": _vehicle_payload(vehicle),
        "dateEffet": _date_or_none(quote.effective_date),
        "dateExpiration": _date_or_none(quote.expiration_date),
        "valeurNeuve": _decimal_or_none(vehicle.new_value),
        "valeurActuelle": _decimal_or_none(vehicle.current_value),
        "garanties": quote.coverage_options or [],
        "periodicite": quote.periodicity,
        "souscripteur": _client_payload(client),
        "typePersonne": "MORALE" if client.client_type == "COMPANY" else "PHYSIQUE",
        "referenceTrxPartner": _payment_reference(contract),
        "responsabiliteCivile": _decimal_or_none(quote.civil_liability_amount),
    }
    return _drop_none(payload)


def build_ass_qrcode_payload_for_product(contract):
    product_type = contract.quote.product_type
    if product_type == "FLEET":
        return build_ass_fleet_qrcode_payload(contract)
    if product_type == "TRAILER":
        return build_ass_trailer_qrcode_payload(contract)
    if product_type == "GARAGE":
        return build_ass_garage_qrcode_payload(contract)
    if product_type == "MOTO":
        return build_ass_moto_qrcode_payload(contract)
    return build_ass_qrcode_payload(contract)


def build_ass_fleet_qrcode_payload(contract):
    quote = contract.quote
    client = contract.client
    return _drop_none(
        {
            "referenceFlotte": _product_data_value(
                quote,
                "referenceFlotte",
                "reference_flotte",
                default=f"HORUS-FLEET-{contract.id:06d}",
            ),
            "dateEffet": _date_or_none(quote.effective_date),
            "duree": quote.duration,
            "periodicite": quote.periodicity,
            "typePersonne": _person_type(client),
            "police": contract.contract_number or f"HORUS-PENDING-{contract.id:06d}",
            "cout_police": _decimal_or_none(quote.fees_amount),
            "remise_rc": 0,
            "souscripteur": _client_payload(client),
            "items": [
                {
                    "responsabiliteCivile": _decimal_or_none(
                        quote.civil_liability_amount
                    ),
                    "referenceTrxPartner": _payment_reference(contract),
                    "assure": _client_payload(client),
                    "vehicule": _vehicle_payload(contract.vehicle),
                }
            ],
        }
    )


def build_ass_trailer_qrcode_payload(contract):
    base_payload = _flat_qrcode_payload(contract)
    quote = contract.quote
    vehicle = contract.vehicle
    base_payload.update(
        {
            "referenceVehicule": _product_data_value(
                quote,
                "referenceVehicule",
                "reference_vehicule",
                default=vehicle.registration_number,
            ),
            "immatriculation": vehicle.registration_number,
            "marque": vehicle.brand,
            "modele": vehicle.model,
        }
    )
    return _drop_none(base_payload)


def build_ass_garage_qrcode_payload(contract):
    quote = contract.quote
    vehicle = contract.vehicle
    base_payload = _flat_qrcode_payload(contract)
    base_payload.update(
        {
            "nombreCarte": _product_data_value(
                quote,
                "nombreCarte",
                "nombre_carte",
                default=1,
            ),
            "immatriculation": vehicle.registration_number,
            "genre": vehicle.genre,
            "valeurNeuve": _decimal_or_none(vehicle.new_value),
            "valeurActuelle": _decimal_or_none(vehicle.current_value),
            "garanties": quote.coverage_options or [],
        }
    )
    return _drop_none(base_payload)


def build_ass_moto_qrcode_payload(contract):
    quote = contract.quote
    payload = _flat_qrcode_payload(contract)
    payload["vehicule"] = _moto_vehicle_payload(contract)
    payload["garanties"] = quote.coverage_options or []
    return _drop_none(payload)


def _flat_qrcode_payload(contract):
    quote = contract.quote
    client = contract.client
    return {
        "responsabiliteCivile": _decimal_or_none(quote.civil_liability_amount),
        "dateEffet": _date_or_none(quote.effective_date),
        "dateExpiration": _date_or_none(quote.expiration_date),
        "police": contract.contract_number or f"HORUS-PENDING-{contract.id:06d}",
        "cout_police": _decimal_or_none(quote.fees_amount),
        "remise_rc": 0,
        "duree": quote.duration,
        "periodicite": quote.periodicity,
        "referenceTrxPartner": _payment_reference(contract),
        "typePersonne": _person_type(client),
        "souscripteur": _client_payload(client),
        "assure": _client_payload(client),
    }


def _client_payload(client):
    return {
        "nom": client.company_name or client.last_name or client.first_name,
        "prenom": "" if client.company_name else client.first_name,
        "cellulaire": client.phone,
        "email": client.email,
    }


def _person_type(client):
    return "MORALE" if client.client_type == "COMPANY" else "PHYSIQUE"


def _vehicle_payload(vehicle):
    return _drop_none(
        {
            "genre": vehicle.genre,
            "marque": vehicle.brand,
            "modele": vehicle.model,
            "chassis": vehicle.chassis_number,
            "energie": vehicle.energy,
            "nombrePlace": vehicle.seats,
            "valeurNeuve": _decimal_or_none(vehicle.new_value),
            "valeurActuelle": _decimal_or_none(vehicle.current_value),
            "immatriculation": vehicle.registration_number,
            "puissanceFiscale": vehicle.fiscal_power,
            "dateMiseCirculation": _date_or_none(vehicle.first_registration_date),
        }
    )


def _moto_vehicle_payload(contract):
    payload = _vehicle_payload(contract.vehicle)
    payload.update(
        {
            "cylindre": _required_product_data(
                contract.quote,
                "cylindre",
                "cylinder",
                label="cylindre",
            ),
            "usage": _required_product_data(
                contract.quote,
                "usage",
                label="usage",
            ),
        }
    )
    return _drop_none(payload)


def _required_product_data(quote, *keys, label):
    value = _product_data_value(quote, *keys)
    if value in (None, ""):
        raise serializers.ValidationError(
            {"ass_product_data": f"{label} est obligatoire pour ce produit ASS."}
        )
    return value


def _product_data_value(quote, *keys, default=None):
    data = quote.ass_product_data or {}
    if not isinstance(data, dict):
        raise serializers.ValidationError(
            {"ass_product_data": "Les donnees produit ASS doivent etre un objet JSON."}
        )
    for key in keys:
        value = data.get(key)
        if value not in (None, ""):
            return value
    return default


def _payment_reference(contract):
    if contract.payment.external_reference:
        return contract.payment.external_reference
    return f"HORUS-PAYMENT-{contract.payment_id}"


def _date_or_none(value):
    if value is None:
        return None
    return value.isoformat()


def _decimal_or_none(value):
    if value is None:
        return None
    if isinstance(value, Decimal):
        if value == value.to_integral_value():
            return int(value)
        return float(value)
    return value


def _drop_none(value):
    if isinstance(value, dict):
        return {
            key: _drop_none(nested_value)
            for key, nested_value in value.items()
            if nested_value is not None and nested_value != ""
        }
    if isinstance(value, list):
        return [_drop_none(item) for item in value]
    return value
