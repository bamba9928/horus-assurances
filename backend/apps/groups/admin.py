from django.contrib import admin

from .models import PartnerGroup


@admin.register(PartnerGroup)
class PartnerGroupAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "status", "created_at"]
    list_filter = ["status"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}
