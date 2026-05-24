from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        "created_at",
        "recipient",
        "client",
        "partner_group",
        "notification_type",
        "title",
        "read_at",
    ]
    list_filter = ["notification_type", "partner_group", "read_at"]
    search_fields = [
        "recipient__username",
        "client__first_name",
        "client__last_name",
        "client__company_name",
        "title",
        "message",
        "target_type",
        "target_id",
    ]
    readonly_fields = [
        "partner_group",
        "recipient",
        "client",
        "notification_type",
        "title",
        "message",
        "target_type",
        "target_id",
        "metadata",
        "read_at",
        "created_at",
    ]
