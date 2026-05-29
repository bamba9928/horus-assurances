from django.contrib import admin

from .models import Vehicle


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = [
        "registration_number",
        "brand",
        "brand_reference",
        "model",
        "client",
        "partner_group",
        "contributor",
        "is_active",
    ]
    list_filter = [
        "energy",
        "brand_reference",
        "genre_reference",
        "energy_reference",
        "partner_group",
        "is_active",
    ]
    search_fields = ["registration_number", "brand", "model", "chassis_number", "genre"]
    autocomplete_fields = [
        "partner_group",
        "client",
        "contributor",
        "created_by",
        "brand_reference",
        "genre_reference",
        "energy_reference",
    ]
