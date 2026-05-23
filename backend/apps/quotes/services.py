from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.db import transaction
from rest_framework import serializers

from apps.ass_api.client import ASSAPIClient

from .ass_payloads import build_ass_rc_payload
from .models import Quote

MONEY_QUANTIZER = Decimal("0.01")

ASS_RC_RESPONSE_KEYS = {
    "civil_liability_amount": (
        "civil_liability_amount",
        "civilLiabilityAmount",
        "responsabiliteCivile",
        "responsabilite_civile",
        "rc",
        "montantRC",
        "data",
    ),
    "premium_amount": (
        "premium_amount",
        "premiumAmount",
        "prime",
        "primeNette",
        "prime_nette",
        "primeRC",
        "prime_rc",
        "PrimeTotaleHorsFrais",
        "primeTotaleHorsFrais",
    ),
    "fees_amount": (
        "fees_amount",
        "feesAmount",
        "cout_police",
        "coutPolice",
        "frais",
        "fraisPolice",
    ),
    "total_amount": (
        "total_amount",
        "totalAmount",
        "total",
        "primeTTC",
        "prime_ttc",
        "PrimeTotale",
        "primeTotale",
        "montantTTC",
        "montant_ttc",
    ),
}


@transaction.atomic
def calculate_quote_with_ass(
    *,
    quote,
    calculation_values=None,
    rc_discount_amount=Decimal("0.00"),
    client=None,
):
    quote = (
        Quote.objects.select_for_update()
        .select_related("partner_group", "client", "vehicle", "contributor")
        .get(pk=quote.pk)
    )

    for field, value in (calculation_values or {}).items():
        setattr(quote, field, value)

    ass_client = client or ASSAPIClient()
    response_payload = ass_client.calculate_rc(
        build_ass_rc_payload(quote, rc_discount_amount=rc_discount_amount),
        partner_group=quote.partner_group,
    )
    amounts = extract_ass_rc_amounts(
        response_payload,
        default_fees_amount=quote.fees_amount,
    )

    quote.civil_liability_amount = amounts["civil_liability_amount"]
    quote.premium_amount = amounts["premium_amount"]
    quote.fees_amount = amounts["fees_amount"]
    quote.total_amount = amounts["total_amount"]
    quote.status = Quote.Status.CALCULATED
    quote.full_clean()
    quote.save(
        update_fields=[
            "coverage_options",
            "periodicity",
            "duration",
            "civil_liability_amount",
            "premium_amount",
            "fees_amount",
            "total_amount",
            "status",
            "updated_at",
        ]
    )
    return quote


def extract_ass_rc_amounts(response_payload, *, default_fees_amount=Decimal("0.00")):
    civil_liability_amount = _find_decimal(
        response_payload,
        ASS_RC_RESPONSE_KEYS["civil_liability_amount"],
    )
    premium_amount = _find_decimal(
        response_payload,
        ASS_RC_RESPONSE_KEYS["premium_amount"],
    )
    fees_amount = _find_decimal(response_payload, ASS_RC_RESPONSE_KEYS["fees_amount"])
    total_amount = _find_decimal(response_payload, ASS_RC_RESPONSE_KEYS["total_amount"])

    if fees_amount is None:
        fees_amount = _to_money(default_fees_amount)
    if total_amount is not None:
        premium_amount = total_amount - fees_amount
    elif premium_amount is None:
        premium_amount = civil_liability_amount
    if civil_liability_amount is None:
        civil_liability_amount = premium_amount

    if premium_amount is None or civil_liability_amount is None:
        raise serializers.ValidationError(
            {"ass_api": "La reponse ASS ne contient pas de montant RC exploitable."}
        )
    if premium_amount < Decimal("0.00"):
        raise serializers.ValidationError(
            {"ass_api": "La reponse ASS contient un total inferieur aux frais."}
        )

    if total_amount is None:
        total_amount = premium_amount + fees_amount

    return {
        "civil_liability_amount": _to_money(civil_liability_amount),
        "premium_amount": _to_money(premium_amount),
        "fees_amount": _to_money(fees_amount),
        "total_amount": _to_money(total_amount),
    }


def _find_decimal(value, keys):
    found_value = _find_decimal_value(
        value,
        {_normalize_key(key) for key in keys},
    )
    if found_value in (None, ""):
        return None
    return _to_money(found_value)


def _find_decimal_value(value, normalized_keys):
    if isinstance(value, dict):
        for key, nested_value in value.items():
            if (
                _normalize_key(key) in normalized_keys
                and nested_value not in (None, "")
                and not isinstance(nested_value, (dict, list, tuple))
            ):
                return nested_value
        for nested_value in value.values():
            found_value = _find_decimal_value(nested_value, normalized_keys)
            if found_value not in (None, ""):
                return found_value

    if isinstance(value, list):
        for item in value:
            found_value = _find_decimal_value(item, normalized_keys)
            if found_value not in (None, ""):
                return found_value

    return None


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
    return str(key).replace("_", "").replace("-", "").lower()


def _to_money(value):
    try:
        decimal_value = Decimal(str(value).replace(" ", "").replace(",", "."))
    except (InvalidOperation, ValueError) as exc:
        raise serializers.ValidationError(
            {"ass_api": "La reponse ASS contient un montant invalide."}
        ) from exc
    if decimal_value < Decimal("0.00"):
        raise serializers.ValidationError(
            {"ass_api": "La reponse ASS contient un montant negatif."}
        )
    return decimal_value.quantize(MONEY_QUANTIZER, rounding=ROUND_HALF_UP)
