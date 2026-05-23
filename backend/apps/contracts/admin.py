from django.contrib import admin

from .models import Contract


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "contract_number",
        "status",
        "partner_group",
        "client",
        "vehicle",
        "contributor",
        "attestation_url",
        "carte_brune_url",
        "issued_at",
    ]
    list_filter = ["status", "partner_group"]
    search_fields = [
        "contract_number",
        "attestation_reference",
        "qr_code_reference",
        "attestation_url",
        "carte_brune_url",
        "client__first_name",
        "client__last_name",
        "client__company_name",
        "vehicle__registration_number",
    ]
    autocomplete_fields = [
        "partner_group",
        "quote",
        "payment",
        "client",
        "vehicle",
        "contributor",
        "created_by",
    ]
