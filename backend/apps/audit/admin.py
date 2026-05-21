from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = [
        "created_at",
        "partner_group",
        "actor",
        "action",
        "target_type",
        "target_id",
    ]
    list_filter = ["action", "partner_group"]
    search_fields = ["target_type", "target_id", "actor__username", "partner_group__name"]
    readonly_fields = [
        "partner_group",
        "actor",
        "action",
        "target_type",
        "target_id",
        "metadata",
        "created_at",
    ]
