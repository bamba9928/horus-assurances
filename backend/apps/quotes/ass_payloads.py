from decimal import Decimal


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
            "cout_police": _decimal_or_zero(quote.fees_amount),
            "remise_rc": _decimal_or_zero(rc_discount_amount),
        }
    )


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
