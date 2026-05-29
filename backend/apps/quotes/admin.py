from django.contrib import admin

from .models import Quote


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = [
        "reference",
        "status",
        "product_type",
        "product_reference",
        "client",
        "vehicle",
        "partner_group",
        "contributor",
        "total_amount",
        "created_at",
    ]
    list_filter = [
        "status",
        "product_type",
        "product_reference",
        "duration_option",
        "periodicity",
        "partner_group",
    ]
    search_fields = [
        "reference",
        "client__first_name",
        "client__last_name",
        "client__company_name",
        "vehicle__registration_number",
    ]
    autocomplete_fields = [
        "partner_group",
        "client",
        "vehicle",
        "contributor",
        "created_by",
        "product_reference",
        "duration_option",
    ]
