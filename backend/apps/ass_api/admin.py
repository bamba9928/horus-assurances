from django.contrib import admin

from .models import ASSAPICallLog


@admin.register(ASSAPICallLog)
class ASSAPICallLogAdmin(admin.ModelAdmin):
    list_display = [
        "created_at",
        "partner_group",
        "contract",
        "method",
        "endpoint",
        "status",
        "http_status_code",
        "duration_ms",
    ]
    list_filter = ["status", "method", "partner_group"]
    search_fields = ["endpoint", "error_message"]
    readonly_fields = [
        "partner_group",
        "contract",
        "endpoint",
        "method",
        "status",
        "http_status_code",
        "request_payload",
        "response_payload",
        "error_message",
        "duration_ms",
        "created_at",
    ]
