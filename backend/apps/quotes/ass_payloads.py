from decimal import Decimal

from rest_framework import serializers


def build_ass_rc_payload_for_product(quote, *, rc_discount_amount=Decimal("0.00")):
    if quote.product_type == "FLEET":
        return build_ass_fleet_rc_payload(
            quote,
            rc_discount_amount=rc_discount_amount,
        )
    if quote.product_type == "TRAILER":
        return build_ass_trailer_rc_payload(quote)
    if quote.product_type == "GARAGE":
        return build_ass_garage_rc_payload(
            quote,
            rc_discount_amount=rc_discount_amount,
        )
    if quote.product_type == "MOTO":
        return build_ass_moto_rc_payload(
            quote,
            rc_discount_amount=rc_discount_amount,
        )
    return build_ass_rc_payload(quote, rc_discount_amount=rc_discount_amount)


def build_ass_rc_payload(quote, *, rc_discount_amount=Decimal("0.00")):
    vehicle = quote.vehicle
    return _drop_none(
        {
            "puissanceFiscale": vehicle.fiscal_power,
            "duree": quote.duration,
            "genre": vehicle.genre,
            "nombrePlace": vehicle.seats,
            "periodicite": quote.periodicity,
            "energie": vehicle.energy,
            "valeurNeuve": _decimal_or_zero(vehicle.new_value),
            "valeurActuelle": _decimal_or_zero(vehicle.current_value),
            "garanties": quote.coverage_options or [],
            "garantiesOptPT": _product_data_value(
                quote,
                "garantiesOptPT",
                "garanties_opt_pt",
            ),
            "garantiesOptAR": _product_data_value(
                quote,
                "garantiesOptAR",
                "garanties_opt_ar",
            ),
            "garantiesOptAS": _product_data_value(
                quote,
                "garantiesOptAS",
                "garanties_opt_as",
            ),
            "cout_police": _decimal_or_zero(quote.fees_amount),
            "remise_rc": _decimal_or_zero(rc_discount_amount),
        }
    )


def build_ass_moto_rc_payload(quote, *, rc_discount_amount=Decimal("0.00")):
    vehicle = quote.vehicle
    return _drop_none(
        {
            "cylindre": _required_product_data(
                quote,
                "cylindre",
                "cylinder",
                label="cylindre",
            ),
            "duree": quote.duration,
            "periodicite": quote.periodicity,
            "genre": vehicle.genre,
            "energie": vehicle.energy,
            "usage": _required_product_data(quote, "usage", label="usage"),
            "nombrePlace": vehicle.seats,
            "cout_police": _decimal_or_zero(quote.fees_amount),
            "remise_rc": _decimal_or_zero(rc_discount_amount),
            "garanties": quote.coverage_options or [],
        }
    )


def build_ass_trailer_rc_payload(quote):
    return _drop_none(
        {
            "duree": quote.duration,
            "periodicite": quote.periodicity,
            "referenceVehicule": _required_product_data(
                quote,
                "referenceVehicule",
                "reference_vehicule",
                label="referenceVehicule",
            ),
        }
    )


def build_ass_garage_rc_payload(quote, *, rc_discount_amount=Decimal("0.00")):
    vehicle = quote.vehicle
    return _drop_none(
        {
            "duree": quote.duration,
            "periodicite": quote.periodicity,
            "genre": vehicle.genre,
            "nombreCarte": _product_data_value(
                quote,
                "nombreCarte",
                "nombre_carte",
                default=1,
            ),
            "cout_police": _decimal_or_zero(quote.fees_amount),
            "remise_rc": _decimal_or_zero(rc_discount_amount),
            "valeurNeuve": _decimal_or_zero(vehicle.new_value),
            "valeurActuelle": _decimal_or_zero(vehicle.current_value),
            "garanties": quote.coverage_options or [],
        }
    )


def build_ass_fleet_rc_payload(quote, *, rc_discount_amount=Decimal("0.00")):
    requests = _product_data_value(quote, "requests")
    if requests is None:
        requests = [_fleet_rc_item(quote)]
    if not isinstance(requests, list):
        raise serializers.ValidationError(
            {"ass_product_data": "requests doit etre une liste pour une flotte ASS."}
        )

    return _drop_none(
        {
            "referenceFlotte": _product_data_value(
                quote,
                "referenceFlotte",
                "reference_flotte",
                default=f"HORUS-FLEET-{quote.id:06d}",
            ),
            "periodicite": quote.periodicity,
            "duree": quote.duration,
            "dateEffet": _date_or_none(quote.effective_date),
            "cout_police": _decimal_or_zero(quote.fees_amount),
            "remise_rc": _decimal_or_zero(rc_discount_amount),
            "requests": requests,
        }
    )


def _fleet_rc_item(quote):
    vehicle = quote.vehicle
    return _drop_none(
        {
            "puissanceFiscale": vehicle.fiscal_power,
            "genre": vehicle.genre,
            "energie": vehicle.energy,
            "requestId": f"HORUS-FLEET-{quote.id:06d}-1",
            "valeurNeuve": _decimal_or_zero(vehicle.new_value),
            "valeurActuelle": _decimal_or_zero(vehicle.current_value),
            "garanties": quote.coverage_options or [],
        }
    )


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


def _date_or_none(value):
    if value is None:
        return None
    return value.isoformat()


def _decimal_or_zero(value):
    if value is None:
        return 0
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
