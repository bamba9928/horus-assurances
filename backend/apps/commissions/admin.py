from django.contrib import admin

from .models import Commission, CommissionRule


@admin.register(CommissionRule)
class CommissionRuleAdmin(admin.ModelAdmin):
    list_display = [
        "partner_group",
        "contributor",
        "percentage_rate",
        "fixed_amount",
        "is_active",
        "updated_at",
    ]
    list_filter = ["is_active", "partner_group"]
    search_fields = ["partner_group__name", "contributor__username"]
    autocomplete_fields = ["partner_group", "contributor"]


@admin.register(Commission)
class CommissionAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "partner_group",
        "contract",
        "contributor",
        "base_amount",
        "percentage_rate",
        "fixed_amount",
        "amount",
        "status",
    ]
    list_filter = ["status", "partner_group"]
    search_fields = ["contract__contract_number", "contributor__username"]
    autocomplete_fields = ["partner_group", "contract", "payment", "contributor", "rule"]
