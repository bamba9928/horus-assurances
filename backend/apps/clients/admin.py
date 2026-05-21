from django.contrib import admin

from .models import Client


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
