from django.contrib import admin

from .models import GroupWallet, Payment, PaymentWebhookEvent, WalletTransaction


@admin.register(GroupWallet)
class GroupWalletAdmin(admin.ModelAdmin):
    list_display = ["partner_group", "balance", "currency", "updated_at"]
    search_fields = ["partner_group__name", "partner_group__slug"]


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = [
        "partner_group",
        "transaction_type",
        "direction",
        "amount",
        "balance_after",
        "reference",
        "created_at",
    ]
    list_filter = ["transaction_type", "direction", "partner_group"]
    search_fields = ["reference", "idempotency_key", "partner_group__name"]
    autocomplete_fields = ["wallet", "partner_group", "created_by"]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "partner_group",
        "quote",
        "method",
        "status",
        "amount",
        "external_reference",
        "confirmed_at",
    ]
    list_filter = ["method", "status", "partner_group"]
    search_fields = ["external_reference", "idempotency_key", "quote__reference"]
    autocomplete_fields = [
        "partner_group",
        "quote",
        "client",
        "contributor",
        "created_by",
        "wallet_transaction",
    ]


@admin.register(PaymentWebhookEvent)
class PaymentWebhookEventAdmin(admin.ModelAdmin):
    list_display = [
        "provider",
        "event_id",
        "event_type",
        "provider_reference",
        "payment",
        "status",
        "received_at",
        "processed_at",
    ]
    list_filter = ["provider", "status"]
    search_fields = [
        "event_id",
        "event_type",
        "provider_reference",
        "payment__external_reference",
    ]
    readonly_fields = [
        "provider",
        "event_id",
        "event_type",
        "provider_reference",
        "payment",
        "status",
        "payload",
        "headers",
        "error_message",
        "received_at",
        "processed_at",
    ]
