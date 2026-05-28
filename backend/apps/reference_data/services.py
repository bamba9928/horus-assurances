def active_reference_value(reference, fallback):
    if reference is not None and getattr(reference, "is_active", False):
        return reference.ass_code or reference.code or fallback
    return fallback


def vehicle_brand_value(vehicle):
    return active_reference_value(
        getattr(vehicle, "brand_reference", None),
        vehicle.brand,
    )


def vehicle_genre_value(vehicle):
    return active_reference_value(
        getattr(vehicle, "genre_reference", None),
        vehicle.genre,
    )


def vehicle_energy_value(vehicle):
    return active_reference_value(
        getattr(vehicle, "energy_reference", None),
        vehicle.energy,
    )


def quote_product_code(quote):
    product_reference = getattr(quote, "product_reference", None)
    if product_reference is not None and product_reference.is_active:
        return product_reference.code or quote.product_type
    return quote.product_type


def quote_duration_value(quote):
    duration_option = getattr(quote, "duration_option", None)
    if duration_option is not None and duration_option.is_active:
        return duration_option.ass_duration or duration_option.duration or quote.duration
    return quote.duration


def quote_periodicity_value(quote):
    duration_option = getattr(quote, "duration_option", None)
    if duration_option is not None and duration_option.is_active:
        return (
            duration_option.ass_periodicity
            or duration_option.periodicity
            or quote.periodicity
        )
    return quote.periodicity


def apply_quote_reference_defaults(quote, *, explicit_fields=None):
    explicit_fields = set(explicit_fields or ())
    product_reference = getattr(quote, "product_reference", None)
    duration_option = getattr(quote, "duration_option", None)

    product_values = getattr(getattr(quote.__class__, "ProductType", None), "values", [])
    if (
        "product_type" not in explicit_fields
        and product_reference is not None
        and product_reference.is_active
        and product_reference.code in product_values
    ):
        quote.product_type = product_reference.code

    if duration_option is not None and duration_option.is_active:
        if "duration" not in explicit_fields:
            quote.duration = duration_option.ass_duration or duration_option.duration
        if "periodicity" not in explicit_fields:
            quote.periodicity = (
                duration_option.ass_periodicity or duration_option.periodicity
            )

    return quote


def mandatory_guarantee_references():
    from .models import GuaranteeReference

    return GuaranteeReference.objects.active().filter(is_mandatory=True)


def default_guarantee_references():
    from .models import GuaranteeReference

    return GuaranteeReference.objects.active().filter(is_default_selected=True)
