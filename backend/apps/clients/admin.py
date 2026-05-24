from django.contrib import admin

from .models import Client, ClientAccessToken


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = [
        "display_name",
        "client_type",
        "phone",
        "partner_group",
        "contributor",
        "is_active",
    ]
    list_filter = ["client_type", "partner_group", "is_active"]
    search_fields = [
        "first_name",
        "last_name",
        "company_name",
        "email",
        "phone",
        "identity_number",
    ]
    autocomplete_fields = ["partner_group", "contributor", "created_by"]


@admin.register(ClientAccessToken)
class ClientAccessTokenAdmin(admin.ModelAdmin):
    list_display = [
        "client",
        "contract",
        "partner_group",
        "delivery_channel",
        "expires_at",
        "revoked_at",
        "used_at",
        "created_at",
    ]
    list_filter = ["delivery_channel", "partner_group", "revoked_at", "expires_at"]
    search_fields = [
        "client__first_name",
        "client__last_name",
        "client__company_name",
        "contract__contract_number",
    ]
    readonly_fields = [
        "partner_group",
        "client",
        "contract",
        "token_hash",
        "delivery_channel",
        "created_by",
        "rotated_from",
        "expires_at",
        "revoked_at",
        "used_at",
        "created_at",
    ]
