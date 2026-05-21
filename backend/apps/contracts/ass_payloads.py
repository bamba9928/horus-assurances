from decimal import Decimal


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


def _client_payload(client):
    return {
        "nom": client.company_name or client.last_name or client.first_name,
        "prenom": "" if client.company_name else client.first_name,
        "cellulaire": client.phone,
        "email": client.email,
    }


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
