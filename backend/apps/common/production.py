from calendar import monthrange
from collections import defaultdict
from datetime import UTC, datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Prefetch, Q
from django.utils import timezone
from rest_framework import serializers

from apps.commissions.models import Commission
from apps.contracts.documents import build_contract_document_items
from apps.contracts.models import Contract
from apps.payments.models import Payment
from apps.quotes.models import Quote
from apps.reference_data.services import quote_product_code

User = get_user_model()
MONEY_QUANTIZER = Decimal("0.01")
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
MAX_EXPORT_ROWS = 5000


def build_production_payload(*, user, query_params):
    filters = _parse_filters(query_params)
    timezone_info = _timezone(filters["timezone"])

    contracts = list(
        _apply_contract_filters(
            _scoped_contract_queryset(user),
            filters,
            timezone_info=timezone_info,
        ).order_by("-created_at", "-id")
    )
    quotes_without_contract = list(
        _apply_quote_filters(
            _scoped_quote_queryset(user),
            filters,
            timezone_info=timezone_info,
        ).order_by("-created_at", "-id")
    )
    entries = [_contract_entry(contract) for contract in contracts]
    entries.extend(_quote_entry(quote) for quote in quotes_without_contract)
    entries = _filter_by_entry_date(entries, filters, timezone_info=timezone_info)
    entries = _filter_by_entry_payment_status(entries, filters["payment_status"])
    entries = _filter_by_trailer(entries, filters["with_trailer"])
    entries.sort(key=_entry_sort_key, reverse=True)

    page_entries, pagination = _paginate_entries(entries, filters)
    return {
        "scope": _scope_name(user),
        "filters": filters,
        "summary": _summary(entries),
        "breakdowns": {
            "daily": _date_breakdown(entries, timezone_info=timezone_info),
            "monthly": _month_breakdown(entries, timezone_info=timezone_info),
            "by_group": _group_breakdown(entries),
            "by_contributor": _contributor_breakdown(entries),
        },
        "count": len(entries),
        "pagination": pagination,
        "results": [_entry_row(entry, timezone_info=timezone_info) for entry in page_entries],
    }


def _parse_filters(query_params):
    return {
        "today": _truthy(query_params.get("today") or query_params.get("jour")),
        "timezone": query_params.get("timezone")
        or query_params.get("tz")
        or settings.TIME_ZONE,
        "month": query_params.get("month") or query_params.get("mois") or "",
        "date_debut": query_params.get("date_debut")
        or query_params.get("start_date")
        or "",
        "date_fin": query_params.get("date_fin") or query_params.get("end_date") or "",
        "contributor": query_params.get("contributor")
        or query_params.get("apporteur")
        or "",
        "group": query_params.get("group") or query_params.get("groupe") or "",
        "contract_status": query_params.get("contract_status")
        or query_params.get("statut_contrat")
        or query_params.get("status")
        or "",
        "payment_status": query_params.get("payment_status")
        or query_params.get("statut_paiement")
        or "",
        "product": query_params.get("product") or query_params.get("produit") or "",
        "registration_number": query_params.get("registration_number")
        or query_params.get("immatriculation")
        or "",
        "client": query_params.get("client") or "",
        "issued": _optional_bool(query_params.get("issued") or query_params.get("emis")),
        "with_trailer": _optional_bool(
            query_params.get("with_trailer") or query_params.get("remorque")
        ),
        "page": _positive_int(query_params.get("page"), default=1, field_name="page"),
        "page_size": _positive_int(
            query_params.get("page_size"),
            default=DEFAULT_PAGE_SIZE,
            field_name="page_size",
            max_value=MAX_PAGE_SIZE,
        ),
        "export": _truthy(query_params.get("export")),
    }


def _scoped_contract_queryset(user):
    queryset = Contract.objects.select_related(
        "partner_group",
        "quote",
        "quote__product_reference",
        "quote__duration_option",
        "payment",
        "client",
        "vehicle",
        "vehicle__genre_reference",
        "contributor",
        "commission",
    )
    if user.is_general_admin:
        return queryset
    if user.is_group_admin:
        return queryset.filter(partner_group=user.partner_group)
    if user.is_contributor:
        return queryset.filter(contributor=user)
    return queryset.none()


def _scoped_quote_queryset(user):
    payments = Payment.objects.order_by("-created_at", "-id")
    queryset = (
        Quote.objects.select_related(
            "partner_group",
            "product_reference",
            "duration_option",
            "client",
            "vehicle",
            "vehicle__genre_reference",
            "contributor",
        )
        .prefetch_related(Prefetch("payments", queryset=payments, to_attr="production_payments"))
        .filter(contract__isnull=True)
    )
    if user.is_general_admin:
        return queryset
    if user.is_group_admin:
        return queryset.filter(partner_group=user.partner_group)
    if user.is_contributor:
        return queryset.filter(contributor=user)
    return queryset.none()


def _apply_contract_filters(queryset, filters, *, timezone_info):
    queryset = _apply_common_filters(queryset, filters, timezone_info=timezone_info)
    if filters["contract_status"]:
        queryset = queryset.filter(status=filters["contract_status"].upper())
    if filters["payment_status"]:
        queryset = queryset.filter(payment__status=filters["payment_status"].upper())
    if filters["issued"] is True:
        queryset = queryset.filter(status=Contract.Status.ISSUED)
    if filters["issued"] is False:
        queryset = queryset.exclude(status=Contract.Status.ISSUED)
    return queryset


def _apply_quote_filters(queryset, filters, *, timezone_info):
    queryset = _apply_common_filters(
        queryset,
        filters,
        timezone_info=timezone_info,
        include_date_filters=False,
    )
    if filters["contract_status"]:
        if filters["contract_status"].upper() not in ("NO_CONTRACT", "WITHOUT_CONTRACT"):
            queryset = queryset.none()
    if filters["payment_status"]:
        queryset = queryset.filter(payments__status=filters["payment_status"].upper()).distinct()
    if filters["issued"] is True:
        queryset = queryset.none()
    return _apply_quote_entry_date_prefilter(
        queryset,
        filters,
        timezone_info=timezone_info,
    )


def _apply_common_filters(
    queryset,
    filters,
    *,
    timezone_info,
    include_date_filters=True,
):
    if include_date_filters:
        queryset = _apply_created_at_filters(
            queryset,
            filters,
            timezone_info=timezone_info,
        )
    if filters["contributor"]:
        queryset = _filter_contributor(queryset, filters["contributor"])
    if filters["group"]:
        queryset = _filter_group(queryset, filters["group"])
    if filters["product"]:
        product = filters["product"].upper()
        queryset = queryset.filter(
            Q(quote__product_type=product) | Q(quote__product_reference__code=product)
            if queryset.model is Contract
            else Q(product_type=product) | Q(product_reference__code=product)
        )
    if filters["registration_number"]:
        lookup = (
            "vehicle__registration_number__icontains"
            if queryset.model is Quote
            else "vehicle__registration_number__icontains"
        )
        queryset = queryset.filter(**{lookup: filters["registration_number"]})
    if filters["client"]:
        client_value = filters["client"]
        queryset = queryset.filter(
            Q(client__first_name__icontains=client_value)
            | Q(client__last_name__icontains=client_value)
            | Q(client__company_name__icontains=client_value)
            | Q(client__phone__icontains=client_value)
        )
    return queryset


def _apply_created_at_filters(queryset, filters, *, timezone_info):
    for start, end in _date_filter_windows(filters, timezone_info=timezone_info):
        if start is not None:
            queryset = queryset.filter(created_at__gte=start)
        if end is not None:
            queryset = queryset.filter(created_at__lt=end)
    return queryset


def _apply_quote_entry_date_prefilter(queryset, filters, *, timezone_info):
    for start, end in _date_filter_windows(filters, timezone_info=timezone_info):
        quote_without_payment = Q(payments__isnull=True)
        payment_date = Q()
        if start is not None:
            quote_without_payment &= Q(created_at__gte=start)
            payment_date &= Q(payments__created_at__gte=start)
        if end is not None:
            quote_without_payment &= Q(created_at__lt=end)
            payment_date &= Q(payments__created_at__lt=end)
        queryset = queryset.filter(quote_without_payment | payment_date).distinct()
    return queryset


def _filter_contributor(queryset, value):
    if str(value).isdigit():
        return queryset.filter(contributor_id=int(value))
    return queryset.filter(contributor__username__icontains=value)


def _filter_group(queryset, value):
    if str(value).isdigit():
        return queryset.filter(partner_group_id=int(value))
    return queryset.filter(
        Q(partner_group__slug=value) | Q(partner_group__name__icontains=value)
    )


def _contract_entry(contract):
    return {
        "entry_type": "CONTRACT",
        "created_at": contract.created_at,
        "contract": contract,
        "quote": contract.quote,
        "payment": contract.payment,
        "partner_group": contract.partner_group,
        "client": contract.client,
        "vehicle": contract.vehicle,
        "contributor": contract.contributor,
    }


def _quote_entry(quote):
    payment = _latest_payment(quote)
    return {
        "entry_type": "PAYMENT" if payment else "QUOTE",
        "created_at": payment.created_at if payment else quote.created_at,
        "contract": None,
        "quote": quote,
        "payment": payment,
        "partner_group": quote.partner_group,
        "client": quote.client,
        "vehicle": quote.vehicle,
        "contributor": quote.contributor,
    }


def _entry_row(entry, *, timezone_info):
    contract = entry["contract"]
    quote = entry["quote"]
    payment = entry["payment"]
    commission = _commission(contract) if contract else None
    documents = (
        build_contract_document_items(contract, include_urls=False) if contract else []
    )
    amount = payment.amount if payment else quote.total_amount
    return {
        "id": contract.id if contract else None,
        "entry_id": _entry_id(entry),
        "entry_type": entry["entry_type"],
        "contract_id": contract.id if contract else None,
        "quote_id": quote.id,
        "payment_id": payment.id if payment else None,
        "contract_reference": contract.contract_number if contract else "",
        "client": entry["client"].display_name,
        "client_phone": entry["client"].phone,
        "vehicle": _vehicle_label(entry["vehicle"]),
        "registration_number": entry["vehicle"].registration_number,
        "product": quote_product_code(quote),
        "contract_status": contract.status if contract else "NO_CONTRACT",
        "payment_status": payment.status if payment else "",
        "amount": _money(amount),
        "commission": _money(commission.amount if commission else Decimal("0.00")),
        "commission_status": commission.status if commission else "",
        "contributor": _user_summary(entry["contributor"]),
        "group": _group_summary(entry["partner_group"]),
        "created_at": timezone.localtime(entry["created_at"], timezone_info).isoformat(),
        "effective_date": _date_or_none(quote.effective_date),
        "expiration_date": _date_or_none(quote.expiration_date),
        "attestation_available": bool(contract and contract.attestation_url),
        "carte_brune_available": bool(contract and contract.carte_brune_url),
        "has_trailer": _entry_has_trailer(entry),
        "documents_available_count": sum(1 for document in documents if document["available"]),
    }


def _summary(entries):
    contract_entries = [entry for entry in entries if entry["contract"] is not None]
    payment_entries = [entry for entry in entries if entry["payment"] is not None]
    return {
        "total_items": len(entries),
        "total_contracts": len(contract_entries),
        "total_quotes_without_contract": sum(
            1 for entry in entries if entry["entry_type"] == "QUOTE"
        ),
        "total_payments_without_contract": sum(
            1 for entry in entries if entry["entry_type"] == "PAYMENT"
        ),
        "issued_contracts": sum(
            1
            for entry in contract_entries
            if entry["contract"].status == Contract.Status.ISSUED
        ),
        "pending_contracts": sum(
            1
            for entry in contract_entries
            if entry["contract"].status
            in (Contract.Status.DRAFT, Contract.Status.READY_TO_ISSUE)
        ),
        "failed_contracts": sum(
            1
            for entry in contract_entries
            if entry["contract"].status == Contract.Status.CANCELLED
            or entry["payment"].status == Payment.Status.FAILED
        ),
        "paid_payments": sum(
            1 for entry in payment_entries if entry["payment"].status == Payment.Status.CONFIRMED
        ),
        "pending_payments": sum(
            1 for entry in payment_entries if entry["payment"].status == Payment.Status.PENDING
        ),
        "failed_payments": sum(
            1 for entry in payment_entries if entry["payment"].status == Payment.Status.FAILED
        ),
        "total_amount": _money(sum((_entry_amount(entry) for entry in entries), Decimal("0.00"))),
        "total_paid_amount": _money(
            sum(
                (
                    _entry_amount(entry)
                    for entry in entries
                    if entry["payment"] is not None
                    and entry["payment"].status == Payment.Status.CONFIRMED
                ),
                Decimal("0.00"),
            )
        ),
        "total_commission_amount": _money(
            sum((_commission_amount(entry["contract"]) for entry in contract_entries), Decimal("0.00"))
        ),
        "contracts_with_trailer": sum(
            1 for entry in contract_entries if _entry_has_trailer(entry)
        ),
        "items_with_trailer": sum(1 for entry in entries if _entry_has_trailer(entry)),
        "documents_available_count": sum(
            _documents_available_count(entry["contract"]) for entry in contract_entries
        ),
    }


def _date_breakdown(entries, *, timezone_info):
    grouped = defaultdict(list)
    for entry in entries:
        grouped[_local_date(entry["created_at"], timezone_info).isoformat()].append(entry)
    return _breakdown(grouped, "date")


def _month_breakdown(entries, *, timezone_info):
    grouped = defaultdict(list)
    for entry in entries:
        date_value = _local_date(entry["created_at"], timezone_info)
        grouped[f"{date_value.year:04d}-{date_value.month:02d}"].append(entry)
    return _breakdown(grouped, "month")


def _group_breakdown(entries):
    grouped = defaultdict(list)
    labels = {}
    for entry in entries:
        key = entry["partner_group"].id
        grouped[key].append(entry)
        labels[key] = {"id": key, "name": entry["partner_group"].name}
    return [
        {**labels[key], **_summary(items)}
        for key, items in sorted(grouped.items(), key=lambda item: labels[item[0]]["name"])
    ]


def _contributor_breakdown(entries):
    grouped = defaultdict(list)
    labels = {}
    for entry in entries:
        user = entry["contributor"]
        key = user.id if user else 0
        grouped[key].append(entry)
        labels[key] = _user_summary(user)
    return [
        {**labels[key], **_summary(items)}
        for key, items in sorted(grouped.items(), key=lambda item: labels[item[0]]["username"])
    ]


def _breakdown(grouped, key_name):
    return [
        {key_name: key, **_summary(items)}
        for key, items in sorted(grouped.items(), key=lambda item: item[0])
    ]


def _paginate_entries(entries, filters):
    if filters["export"]:
        export_entries = entries[:MAX_EXPORT_ROWS]
        return export_entries, {
            "page": 1,
            "page_size": len(export_entries),
            "total_count": len(entries),
            "total_pages": 1,
            "has_next": False,
            "has_previous": False,
            "export": True,
            "max_export_rows": MAX_EXPORT_ROWS,
            "truncated": len(entries) > MAX_EXPORT_ROWS,
        }

    page = filters["page"]
    page_size = filters["page_size"]
    total_count = len(entries)
    total_pages = max(1, (total_count + page_size - 1) // page_size)
    if page > total_pages:
        page_entries = []
    else:
        start = (page - 1) * page_size
        page_entries = entries[start : start + page_size]
    return page_entries, {
        "page": page,
        "page_size": page_size,
        "total_count": total_count,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_previous": page > 1 and total_count > 0,
        "export": False,
        "max_export_rows": MAX_EXPORT_ROWS,
        "truncated": False,
    }


def _filter_by_trailer(entries, with_trailer):
    if with_trailer is None:
        return entries
    return [entry for entry in entries if _entry_has_trailer(entry) is with_trailer]


def _filter_by_entry_date(entries, filters, *, timezone_info):
    windows = _date_filter_windows(filters, timezone_info=timezone_info)
    if not windows:
        return entries
    return [
        entry
        for entry in entries
        if _datetime_matches_windows(entry["created_at"], windows)
    ]


def _filter_by_entry_payment_status(entries, payment_status):
    if not payment_status:
        return entries
    normalized_status = payment_status.upper()
    return [
        entry
        for entry in entries
        if entry["payment"] is not None
        and entry["payment"].status == normalized_status
    ]


def _entry_has_trailer(entry):
    quote = entry["quote"]
    if quote_product_code(quote) == Quote.ProductType.TRAILER:
        return True
    data = quote.ass_product_data or {}
    if isinstance(data, dict) and any(
        data.get(key) for key in ("referenceVehicule", "reference_vehicule")
    ):
        return True
    genre = getattr(entry["vehicle"], "genre_reference", None)
    if genre is not None and genre.code == "REMORQUE":
        return True
    return str(entry["vehicle"].genre or "").strip().upper() == "REMORQUE"


def _entry_amount(entry):
    if entry["payment"] is not None:
        return entry["payment"].amount
    return entry["quote"].total_amount


def _entry_sort_key(entry):
    return (entry["created_at"], _entry_id(entry))


def _entry_id(entry):
    if entry["contract"] is not None:
        return f"contract-{entry['contract'].id}"
    if entry["payment"] is not None:
        return f"payment-{entry['payment'].id}"
    return f"quote-{entry['quote'].id}"


def _latest_payment(quote):
    payments = getattr(quote, "production_payments", None)
    if payments is not None:
        return payments[0] if payments else None
    return quote.payments.order_by("-created_at", "-id").first()


def _datetime_matches_windows(value, windows):
    for start, end in windows:
        if start is not None and value < start:
            return False
        if end is not None and value >= end:
            return False
    return True


def _commission(contract):
    if contract is None:
        return None
    try:
        return contract.commission
    except Commission.DoesNotExist:
        return None


def _commission_amount(contract):
    commission = _commission(contract)
    return commission.amount if commission else Decimal("0.00")


def _documents_available_count(contract):
    return sum(
        1
        for document in build_contract_document_items(contract, include_urls=False)
        if document["available"]
    )


def _vehicle_label(vehicle):
    return f"{vehicle.brand} {vehicle.model}".strip()


def _user_summary(user):
    if user is None:
        return {"id": None, "username": "", "display_name": ""}
    display_name = user.get_full_name() or user.username
    return {"id": user.id, "username": user.username, "display_name": display_name}


def _group_summary(group):
    return {"id": group.id, "name": group.name, "slug": group.slug}


def _scope_name(user):
    if user.is_general_admin:
        return "platform"
    if user.is_group_admin:
        return "group"
    if user.is_contributor:
        return "contributor"
    return "none"


def _timezone(value):
    try:
        return ZoneInfo(value)
    except ZoneInfoNotFoundError as exc:
        raise serializers.ValidationError({"filters": f"Timezone invalide: {value}"}) from exc


def _today(timezone_info):
    return timezone.now().astimezone(timezone_info).date()


def _date_bounds(date_value, timezone_info):
    start = datetime.combine(date_value, time.min, tzinfo=timezone_info)
    end = start + timedelta(days=1)
    return start.astimezone(UTC), end.astimezone(UTC)


def _date_filter_windows(filters, *, timezone_info):
    windows = []
    if filters["today"]:
        windows.append(_date_bounds(_today(timezone_info), timezone_info))
    if filters["month"]:
        windows.append(_month_bounds(filters["month"], timezone_info))
    if filters["date_debut"]:
        start, _ = _date_bounds(
            _parse_date(filters["date_debut"], "date_debut"),
            timezone_info,
        )
        windows.append((start, None))
    if filters["date_fin"]:
        _, end = _date_bounds(
            _parse_date(filters["date_fin"], "date_fin"),
            timezone_info,
        )
        windows.append((None, end))
    return windows


def _month_bounds(value, timezone_info):
    year, month = _parse_month(value)
    start = datetime(year, month, 1, tzinfo=timezone_info)
    end = start + timedelta(days=monthrange(year, month)[1])
    return start.astimezone(UTC), end.astimezone(UTC)


def _local_date(value, timezone_info):
    return timezone.localtime(value, timezone_info).date()


def _truthy(value):
    return str(value).strip().lower() in ("1", "true", "yes", "oui", "on")


def _optional_bool(value):
    if value in (None, ""):
        return None
    normalized = str(value).strip().lower()
    if normalized in ("1", "true", "yes", "oui", "on"):
        return True
    if normalized in ("0", "false", "no", "non", "off"):
        return False
    raise serializers.ValidationError({"filters": f"Booleen invalide: {value}"})


def _positive_int(value, *, default, field_name, max_value=None):
    if value in (None, ""):
        return default
    try:
        normalized = int(value)
    except (TypeError, ValueError) as exc:
        raise serializers.ValidationError(
            {"filters": f"{field_name} doit etre un entier positif."}
        ) from exc
    if normalized <= 0:
        raise serializers.ValidationError(
            {"filters": f"{field_name} doit etre un entier positif."}
        )
    if max_value is not None:
        return min(normalized, max_value)
    return normalized


def _parse_date(value, field_name):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError) as exc:
        raise serializers.ValidationError(
            {"filters": f"{field_name} doit etre au format YYYY-MM-DD."}
        ) from exc


def _parse_month(value):
    try:
        month_value = datetime.strptime(value, "%Y-%m")
    except (TypeError, ValueError) as exc:
        raise serializers.ValidationError(
            {"filters": "month/mois doit etre au format YYYY-MM."}
        ) from exc
    return month_value.year, month_value.month


def _date_or_none(value):
    return value.isoformat() if value else None


def _money(value):
    return str(Decimal(value or 0).quantize(MONEY_QUANTIZER))
