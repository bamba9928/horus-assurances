import calendar
from datetime import timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.db import models, transaction
from rest_framework import serializers

from apps.ass_api.client import ASSAPIClient
from apps.contracts.documents import build_quote_expected_document_items
from apps.commissions.services import (
    calculate_commission_amount,
    get_applicable_commission_rule,
)
from apps.contracts.models import Contract
from apps.payments.models import Payment
from apps.reference_data.models import (
    FormRule,
    GuaranteeReference,
    ProductReference,
    VehicleGenre,
)
from apps.reference_data.services import (
    apply_quote_reference_defaults,
    mandatory_guarantee_references,
    quote_duration_value,
    quote_periodicity_value,
    quote_product_code,
    vehicle_brand_value,
    vehicle_energy_value,
    vehicle_genre_value,
)

from .ass_payloads import build_ass_rc_payload_for_product
from .models import Quote

MONEY_QUANTIZER = Decimal("0.01")

ASS_RC_METHOD_BY_PRODUCT_TYPE = {
    Quote.ProductType.AUTO: "calculate_rc",
    Quote.ProductType.MOTO: "calculate_moto_rc",
    Quote.ProductType.FLEET: "calculate_fleet_rc",
    Quote.ProductType.TRAILER: "calculate_trailer_rc",
    Quote.ProductType.SCHOOL_BUS: "calculate_school_bus_rc",
    Quote.ProductType.GARAGE: "calculate_garage_rc",
}

ASS_RC_ENDPOINT_BY_PRODUCT_TYPE = {
    Quote.ProductType.AUTO: "/api/v1/partner/rc.request",
    Quote.ProductType.MOTO: "/api/v1/partner/rc.moto",
    Quote.ProductType.FLEET: "/api/v1/partner/rc.flotte.request",
    Quote.ProductType.TRAILER: "/api/v1/partner/remorque.rc.request",
    Quote.ProductType.SCHOOL_BUS: "/api/v1/partner/bus.ecole.rc",
    Quote.ProductType.GARAGE: "/api/v1/partner/rc.garage",
}

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
        .select_related(
            "partner_group",
            "client",
            "vehicle",
            "contributor",
            "product_reference",
            "duration_option",
            "vehicle__brand_reference",
            "vehicle__genre_reference",
            "vehicle__energy_reference",
        )
        .get(pk=quote.pk)
    )

    explicit_fields = set((calculation_values or {}).keys())
    for field, value in (calculation_values or {}).items():
        setattr(quote, field, value)
    apply_quote_reference_defaults(quote, explicit_fields=explicit_fields)

    ass_client = client or ASSAPIClient()
    product_code = quote_product_code(quote)
    method_name = ASS_RC_METHOD_BY_PRODUCT_TYPE.get(
        product_code,
        "calculate_rc",
    )
    response_payload = getattr(ass_client, method_name)(
        build_ass_rc_payload_for_product(
            quote,
            rc_discount_amount=rc_discount_amount,
        ),
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
            "ass_product_data",
            "product_type",
            "product_reference",
            "duration_option",
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


def build_quote_ass_payload_preview(
    *,
    quote,
    rc_discount_amount=Decimal("0.00"),
):
    product_type = quote_product_code(quote)
    return {
        "preview_only": True,
        "operation": "rc_calculation",
        "product_type": product_type,
        "ass_method": ASS_RC_METHOD_BY_PRODUCT_TYPE.get(
            product_type,
            "calculate_rc",
        ),
        "ass_endpoint": ASS_RC_ENDPOINT_BY_PRODUCT_TYPE.get(
            product_type,
            "/api/v1/partner/rc.request",
        ),
        "payload": build_ass_rc_payload_for_product(
            quote,
            rc_discount_amount=rc_discount_amount,
        ),
    }


def build_quote_summary(*, quote):
    vehicle = quote.vehicle
    client = quote.client
    payment = _latest_payment(quote)
    contract = _quote_contract(quote)
    commission_summary = _commission_summary(quote)
    trailer_rule = _trailer_rule_summary(quote)
    expiration_date = quote.expiration_date or _calculate_expiration_date(
        effective_date=quote.effective_date,
        duration=quote_duration_value(quote),
        periodicity=quote_periodicity_value(quote),
    )

    return {
        "id": quote.id,
        "reference": str(quote.reference),
        "status": quote.status,
        "client": _client_summary(client),
        "vehicle": _vehicle_summary(vehicle),
        "references": {
            "brand": _reference_summary(
                getattr(vehicle, "brand_reference", None),
                fallback_value=vehicle.brand,
                resolved_value=vehicle_brand_value(vehicle),
            ),
            "genre": _genre_reference_summary(
                quote,
                fallback_value=vehicle.genre,
                resolved_value=vehicle_genre_value(vehicle),
            ),
            "energy": _reference_summary(
                getattr(vehicle, "energy_reference", None),
                fallback_value=vehicle.energy,
                resolved_value=vehicle_energy_value(vehicle),
            ),
            "product": _product_reference_summary(quote),
            "duration": _duration_reference_summary(quote),
        },
        "validity": {
            "effective_date": _date_or_none(quote.effective_date),
            "expiration_date": _date_or_none(expiration_date),
            "expiration_source": "stored" if quote.expiration_date else "calculated",
            "duration": quote_duration_value(quote),
            "periodicity": quote_periodicity_value(quote),
        },
        "guarantees": _guarantee_summary(quote),
        "amounts": {
            "civil_liability_amount": _money(quote.civil_liability_amount),
            "premium_amount": _money(quote.premium_amount),
            "fees_amount": _money(quote.fees_amount),
            "contributor_commission_amount": _money(
                commission_summary["contributor_commission_amount"]
            ),
            "group_commission_amount": _money(
                commission_summary["group_commission_amount"]
            ),
            "commission_total_amount": _money(commission_summary["total_amount"]),
            "net_to_pay_after_commission": _money(
                commission_summary["net_to_pay_after_commission"]
            ),
            "total_to_pay": _money(quote.total_amount),
        },
        "commission": commission_summary,
        "payment": _payment_summary(payment),
        "trailer_rule": trailer_rule,
        "expected_documents": _expected_documents_summary(
            quote=quote,
            contract=contract,
        ),
        "can_issue": _can_issue_summary(quote=quote, payment=payment, contract=contract),
    }


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


def _client_summary(client):
    return {
        "id": client.id,
        "client_type": client.client_type,
        "display_name": client.display_name,
        "first_name": client.first_name,
        "last_name": client.last_name,
        "company_name": client.company_name,
        "phone": client.phone,
        "email": client.email,
    }


def _vehicle_summary(vehicle):
    return {
        "id": vehicle.id,
        "registration_number": vehicle.registration_number,
        "brand": vehicle.brand,
        "model": vehicle.model,
        "chassis_number": vehicle.chassis_number,
        "genre": vehicle.genre,
        "energy": vehicle.energy,
        "fiscal_power": vehicle.fiscal_power,
        "seats": vehicle.seats,
        "first_registration_date": _date_or_none(vehicle.first_registration_date),
        "new_value": _money_or_none(vehicle.new_value),
        "current_value": _money_or_none(vehicle.current_value),
    }


def _reference_summary(reference, *, fallback_value, resolved_value):
    if reference is not None and reference.is_active:
        return {
            "id": reference.id,
            "code": reference.code,
            "ass_code": reference.ass_code,
            "label": reference.label,
            "value": resolved_value,
            "source": "reference",
        }
    return {
        "id": None,
        "code": fallback_value,
        "ass_code": "",
        "label": fallback_value,
        "value": fallback_value,
        "source": "legacy",
    }


def _genre_reference_summary(quote, *, fallback_value, resolved_value):
    genre = getattr(quote.vehicle, "genre_reference", None)
    summary = _reference_summary(
        genre,
        fallback_value=fallback_value,
        resolved_value=resolved_value,
    )
    if genre is not None and genre.is_active:
        summary["category"] = _related_reference_summary(genre.category)
        summary["subcategory"] = _related_reference_summary(genre.subcategory)
        summary["requires_trailer_section"] = genre.requires_trailer_section
    else:
        summary["category"] = None
        summary["subcategory"] = None
        summary["requires_trailer_section"] = False
    return summary


def _product_reference_summary(quote):
    product = getattr(quote, "product_reference", None)
    if product is not None and product.is_active:
        return {
            "id": product.id,
            "code": product.code,
            "ass_code": product.ass_code,
            "label": product.label,
            "value": product.code,
            "source": "reference",
        }
    return {
        "id": None,
        "code": quote.product_type,
        "ass_code": "",
        "label": quote.product_type,
        "value": quote.product_type,
        "source": "legacy",
    }


def _duration_reference_summary(quote):
    duration_option = getattr(quote, "duration_option", None)
    duration = quote_duration_value(quote)
    periodicity = quote_periodicity_value(quote)
    if duration_option is not None and duration_option.is_active:
        return {
            "id": duration_option.id,
            "code": duration_option.code,
            "ass_code": duration_option.ass_code,
            "label": duration_option.label,
            "duration": duration,
            "periodicity": periodicity,
            "source": "reference",
        }
    return {
        "id": None,
        "code": None,
        "ass_code": "",
        "label": f"{duration} {periodicity}",
        "duration": duration,
        "periodicity": periodicity,
        "source": "legacy",
    }


def _related_reference_summary(reference):
    if reference is None:
        return None
    return {
        "id": reference.id,
        "code": reference.code,
        "ass_code": reference.ass_code,
        "label": reference.label,
    }


def _guarantee_summary(quote):
    selected_values = quote.coverage_options or []
    selected_keys = {_coverage_key(value) for value in selected_values}
    mandatory = [
        _guarantee_reference_summary(guarantee, selected=True)
        for guarantee in mandatory_guarantee_references().order_by(
            "sort_order",
            "label",
            "id",
        )
    ]
    optional = [
        _guarantee_reference_summary(
            guarantee,
            selected=_guarantee_is_selected(guarantee, selected_keys),
        )
        for guarantee in GuaranteeReference.objects.active()
        .filter(is_mandatory=False)
        .order_by("sort_order", "label", "id")
    ]
    return {
        "mandatory": mandatory,
        "optional": optional,
        "selected_coverage_options": selected_values,
    }


def _guarantee_reference_summary(guarantee, *, selected):
    return {
        "id": guarantee.id,
        "code": guarantee.code,
        "ass_code": guarantee.ass_code,
        "ass_id": guarantee.ass_id,
        "label": guarantee.label,
        "is_mandatory": guarantee.is_mandatory,
        "is_default_selected": guarantee.is_default_selected,
        "is_readonly": guarantee.is_readonly,
        "selected": selected,
        "payload_value": (
            guarantee.ass_id
            if guarantee.ass_id is not None
            else guarantee.ass_code or guarantee.code
        ),
    }


def _guarantee_is_selected(guarantee, selected_keys):
    candidates = {
        _coverage_key(guarantee.ass_id),
        _coverage_key(guarantee.ass_code),
        _coverage_key(guarantee.code),
    }
    candidates.discard("")
    return bool(candidates & selected_keys)


def _coverage_key(value):
    if value is None:
        return ""
    return str(value).strip().upper()


def _commission_summary(quote):
    rule = get_applicable_commission_rule(
        partner_group=quote.partner_group,
        contributor=quote.contributor,
    )
    percentage_rate = rule.percentage_rate if rule else Decimal("0.0000")
    fixed_amount = rule.fixed_amount if rule else Decimal("0.00")
    if fixed_amount > quote.fees_amount:
        amount = Decimal("0.00")
        warning = "Le fixe commission configure depasse les frais du devis."
    else:
        amount = calculate_commission_amount(
            base_amount=quote.premium_amount,
            percentage_rate=percentage_rate,
            fixed_amount=fixed_amount,
        )
        warning = ""

    if amount > quote.total_amount:
        amount = Decimal("0.00")
        warning = "La commission configuree depasse le total du devis."

    contributor_amount = amount if quote.contributor_id else Decimal("0.00")
    group_amount = amount if not quote.contributor_id and rule else Decimal("0.00")
    total_amount = (contributor_amount + group_amount).quantize(
        MONEY_QUANTIZER,
        rounding=ROUND_HALF_UP,
    )
    net_to_pay_after_commission = (quote.total_amount - total_amount).quantize(
        MONEY_QUANTIZER,
        rounding=ROUND_HALF_UP,
    )

    return {
        "rule_id": rule.id if rule else None,
        "rule_scope": _commission_rule_scope(rule),
        "percentage_rate": _rate(percentage_rate),
        "fixed_amount": _money(fixed_amount),
        "base_amount": _money(quote.premium_amount),
        "contributor_id": quote.contributor_id,
        "contributor_username": quote.contributor.username if quote.contributor_id else "",
        "contributor_commission_amount": contributor_amount,
        "group_commission_amount": group_amount,
        "total_amount": total_amount,
        "net_to_pay_after_commission": net_to_pay_after_commission,
        "warning": warning,
    }


def _commission_rule_scope(rule):
    if rule is None:
        return "none"
    if rule.contributor_id:
        return "contributor"
    return "group"


def _latest_payment(quote):
    prefetched = getattr(quote, "_prefetched_objects_cache", {}).get("payments")
    if prefetched is not None:
        if not prefetched:
            return None
        return sorted(prefetched, key=lambda payment: payment.id, reverse=True)[0]
    return (
        Payment.objects.filter(quote=quote)
        .select_related("contributor")
        .order_by("-id")
        .first()
    )


def _quote_contract(quote):
    try:
        return quote.contract
    except Contract.DoesNotExist:
        return None


def _payment_summary(payment):
    if payment is None:
        return {
            "exists": False,
            "id": None,
            "method": "",
            "status": "",
            "amount": "0.00",
            "currency": "XOF",
            "external_reference": "",
            "confirmed_at": None,
        }
    return {
        "exists": True,
        "id": payment.id,
        "method": payment.method,
        "status": payment.status,
        "amount": _money(payment.amount),
        "currency": payment.currency,
        "external_reference": payment.external_reference,
        "confirmed_at": (
            payment.confirmed_at.isoformat() if payment.confirmed_at else None
        ),
    }


def _trailer_rule_summary(quote):
    genre = _resolve_vehicle_genre_reference(quote.vehicle)
    product = _resolve_product_reference(quote)
    rules = [
        rule
        for rule in FormRule.objects.active()
        .filter(field_name="trailer_section", rule_type=FormRule.RuleType.SHOW)
        .select_related("product", "category", "subcategory", "genre")
        .order_by("priority", "code", "id")
        if _form_rule_matches(rule, product=product, genre=genre)
    ]
    if rules:
        return {
            "visible": True,
            "source": "form_rule",
            "genre_requires_trailer_section": bool(
                genre and genre.requires_trailer_section
            ),
            "matched_rules": [_form_rule_summary(rule) for rule in rules],
        }
    if genre is not None and genre.is_active and genre.requires_trailer_section:
        return {
            "visible": True,
            "source": "vehicle_genre.requires_trailer_section",
            "genre_requires_trailer_section": True,
            "matched_rules": [],
        }
    return {
        "visible": False,
        "source": "none",
        "genre_requires_trailer_section": bool(
            genre and genre.is_active and genre.requires_trailer_section
        ),
        "matched_rules": [],
    }


def _form_rule_matches(rule, *, product, genre):
    if rule.product_id and (product is None or rule.product_id != product.id):
        return False
    if rule.genre_id and (genre is None or rule.genre_id != genre.id):
        return False
    if rule.category_id and (genre is None or rule.category_id != genre.category_id):
        return False
    if rule.subcategory_id and (
        genre is None or rule.subcategory_id != genre.subcategory_id
    ):
        return False
    return True


def _form_rule_summary(rule):
    return {
        "id": rule.id,
        "code": rule.code,
        "field_name": rule.field_name,
        "rule_type": rule.rule_type,
        "value": rule.value,
        "priority": rule.priority,
        "product_code": rule.product.code if rule.product_id else None,
        "category_code": rule.category.code if rule.category_id else None,
        "subcategory_code": rule.subcategory.code if rule.subcategory_id else None,
        "genre_code": rule.genre.code if rule.genre_id else None,
    }


def _expected_documents_summary(*, quote, contract):
    documents = build_quote_expected_document_items(
        quote=quote,
        contract=contract,
        include_urls=False,
    )
    return [
        {
            **document,
            "expected_after_issue": document["required_after_issue"],
        }
        for document in documents
    ]


def _can_issue_summary(*, quote, payment, contract):
    reasons = []
    if quote.total_amount <= Decimal("0.00"):
        reasons.append("Le total du devis doit etre strictement positif.")
    if payment is None:
        reasons.append("Aucun paiement n'est rattache au devis.")
    elif payment.status != Payment.Status.CONFIRMED:
        reasons.append("Le paiement doit etre confirme.")
    if contract is not None and contract.status == Contract.Status.ISSUED:
        reasons.append("Le contrat est deja emis.")
    if contract is not None and contract.status == Contract.Status.CANCELLED:
        reasons.append("Le contrat est annule.")

    return {
        "allowed": not reasons,
        "reasons": reasons,
        "requires_contract_creation": contract is None,
        "contract_id": contract.id if contract else None,
        "contract_status": contract.status if contract else "",
    }


def _resolve_vehicle_genre_reference(vehicle):
    genre_reference = getattr(vehicle, "genre_reference", None)
    if genre_reference is not None and genre_reference.is_active:
        return genre_reference
    genre_value = str(vehicle.genre or "").strip()
    if not genre_value:
        return None
    return (
        VehicleGenre.objects.active()
        .filter(
            models.Q(code__iexact=genre_value)
            | models.Q(ass_code__iexact=genre_value)
            | models.Q(label__iexact=genre_value)
        )
        .select_related("category", "subcategory")
        .first()
    )


def _resolve_product_reference(quote):
    product_reference = getattr(quote, "product_reference", None)
    if product_reference is not None and product_reference.is_active:
        return product_reference
    product_code = str(quote.product_type or "").strip()
    if not product_code:
        return None
    return ProductReference.objects.active().filter(code__iexact=product_code).first()


def _calculate_expiration_date(*, effective_date, duration, periodicity):
    if effective_date is None or duration in (None, "") or not periodicity:
        return None
    try:
        duration = int(duration)
    except (TypeError, ValueError):
        return None
    if duration <= 0:
        return None
    if periodicity == Quote.Periodicity.DAYS:
        return effective_date + timedelta(days=duration) - timedelta(days=1)
    if periodicity == Quote.Periodicity.MONTHS:
        return _add_months(effective_date, duration) - timedelta(days=1)
    if periodicity == Quote.Periodicity.YEARS:
        return _add_months(effective_date, duration * 12) - timedelta(days=1)
    return None


def _add_months(value, months):
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return value.replace(year=year, month=month, day=day)


def _date_or_none(value):
    if value is None:
        return None
    return value.isoformat()


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


def _money(value):
    if value is None:
        value = Decimal("0.00")
    return str(_to_money(value))


def _money_or_none(value):
    if value is None:
        return None
    return _money(value)


def _rate(value):
    return str(Decimal(value).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP))
