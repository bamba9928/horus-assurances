from rest_framework import serializers


class DashboardCountsSerializer(serializers.Serializer):
    groups = serializers.IntegerField()
    users = serializers.IntegerField()
    contributors = serializers.IntegerField()
    clients = serializers.IntegerField()
    vehicles = serializers.IntegerField()
    quotes = serializers.IntegerField()
    payments = serializers.IntegerField()
    confirmed_payments = serializers.IntegerField()
    contracts = serializers.IntegerField()
    issued_contracts = serializers.IntegerField()
    commissions = serializers.IntegerField()
    wallets = serializers.IntegerField()
    audit_logs = serializers.IntegerField()
    unread_notifications = serializers.IntegerField()


class DashboardSerializer(serializers.Serializer):
    scope = serializers.CharField()
    counts = DashboardCountsSerializer()


class ProductionSummarySerializer(serializers.Serializer):
    total_items = serializers.IntegerField()
    total_contracts = serializers.IntegerField()
    total_quotes_without_contract = serializers.IntegerField()
    total_payments_without_contract = serializers.IntegerField()
    issued_contracts = serializers.IntegerField()
    pending_contracts = serializers.IntegerField()
    failed_contracts = serializers.IntegerField()
    paid_payments = serializers.IntegerField()
    pending_payments = serializers.IntegerField()
    failed_payments = serializers.IntegerField()
    total_amount = serializers.CharField()
    total_paid_amount = serializers.CharField()
    total_commission_amount = serializers.CharField()
    contracts_with_trailer = serializers.IntegerField()
    items_with_trailer = serializers.IntegerField()
    documents_available_count = serializers.IntegerField()


class ProductionDateBreakdownSerializer(
    ProductionSummarySerializer,
):
    date = serializers.DateField()


class ProductionMonthBreakdownSerializer(
    ProductionSummarySerializer,
):
    month = serializers.CharField()


class ProductionGroupBreakdownSerializer(
    ProductionSummarySerializer,
):
    id = serializers.IntegerField()
    name = serializers.CharField()


class ProductionUserSummarySerializer(serializers.Serializer):
    id = serializers.IntegerField(allow_null=True)
    username = serializers.CharField(allow_blank=True)
    display_name = serializers.CharField(allow_blank=True)


class ProductionContributorBreakdownSerializer(
    ProductionUserSummarySerializer,
    ProductionSummarySerializer,
):
    pass


class ProductionBreakdownsSerializer(serializers.Serializer):
    daily = ProductionDateBreakdownSerializer(many=True)
    monthly = ProductionMonthBreakdownSerializer(many=True)
    by_group = ProductionGroupBreakdownSerializer(many=True)
    by_contributor = ProductionContributorBreakdownSerializer(many=True)


class ProductionGroupSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    slug = serializers.SlugField()


class ProductionRowSerializer(serializers.Serializer):
    id = serializers.IntegerField(allow_null=True)
    entry_id = serializers.CharField()
    entry_type = serializers.ChoiceField(choices=("CONTRACT", "QUOTE", "PAYMENT"))
    contract_id = serializers.IntegerField(allow_null=True)
    quote_id = serializers.IntegerField()
    payment_id = serializers.IntegerField(allow_null=True)
    contract_reference = serializers.CharField(allow_blank=True)
    client = serializers.CharField()
    client_phone = serializers.CharField(allow_blank=True)
    vehicle = serializers.CharField(allow_blank=True)
    registration_number = serializers.CharField(allow_blank=True)
    product = serializers.CharField()
    contract_status = serializers.CharField()
    payment_status = serializers.CharField(allow_blank=True)
    amount = serializers.CharField()
    commission = serializers.CharField()
    commission_status = serializers.CharField(allow_blank=True)
    contributor = ProductionUserSummarySerializer()
    group = ProductionGroupSerializer()
    created_at = serializers.DateTimeField()
    effective_date = serializers.DateField(allow_null=True)
    expiration_date = serializers.DateField(allow_null=True)
    attestation_available = serializers.BooleanField()
    carte_brune_available = serializers.BooleanField()
    has_trailer = serializers.BooleanField()
    documents_available_count = serializers.IntegerField()


class ProductionPaginationSerializer(serializers.Serializer):
    page = serializers.IntegerField()
    page_size = serializers.IntegerField()
    total_count = serializers.IntegerField()
    total_pages = serializers.IntegerField()
    has_next = serializers.BooleanField()
    has_previous = serializers.BooleanField()
    export = serializers.BooleanField()
    max_export_rows = serializers.IntegerField()
    truncated = serializers.BooleanField()


class ProductionSerializer(serializers.Serializer):
    scope = serializers.CharField()
    filters = serializers.DictField()
    summary = ProductionSummarySerializer()
    breakdowns = ProductionBreakdownsSerializer()
    count = serializers.IntegerField()
    pagination = ProductionPaginationSerializer()
    results = ProductionRowSerializer(many=True)
