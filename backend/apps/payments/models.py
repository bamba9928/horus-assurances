from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from apps.ass_api.sanitizers import sanitize_error_message, sanitize_value


class GroupWallet(models.Model):
    partner_group = models.OneToOneField(
        "groups.PartnerGroup",
        on_delete=models.PROTECT,
        related_name="wallet",
    )
    balance = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    currency = models.CharField(max_length=3, default="XOF")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return f"Wallet {self.partner_group} ({self.balance} {self.currency})"

    def clean(self):
        super().clean()
        if self.balance < Decimal("0.00"):
            raise ValidationError({"balance": "Le solde wallet ne peut pas etre negatif."})


class WalletTransaction(models.Model):
    class TransactionType(models.TextChoices):
        TOP_UP = "TOP_UP", "Recharge"
        DEBIT = "DEBIT", "Debit"
        PAYMENT = "PAYMENT", "Paiement"
        ADJUSTMENT = "ADJUSTMENT", "Ajustement"

    class Direction(models.TextChoices):
        CREDIT = "CREDIT", "Credit"
        DEBIT = "DEBIT", "Debit"

    wallet = models.ForeignKey(
        GroupWallet,
        on_delete=models.PROTECT,
        related_name="transactions",
    )
    partner_group = models.ForeignKey(
        "groups.PartnerGroup",
        on_delete=models.PROTECT,
        related_name="wallet_transactions",
    )
    transaction_type = models.CharField(max_length=20, choices=TransactionType.choices)
    direction = models.CharField(max_length=10, choices=Direction.choices)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    balance_after = models.DecimalField(max_digits=14, decimal_places=2)
    idempotency_key = models.CharField(max_length=120, blank=True)
    reference = models.CharField(max_length=120, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="created_wallet_transactions",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(
                fields=["partner_group", "idempotency_key"],
                condition=~Q(idempotency_key=""),
                name="wallet_transaction_unique_idempotency_per_group",
            )
        ]

    def __str__(self) -> str:
        return f"{self.direction} {self.amount} {self.partner_group}"

    def clean(self):
        super().clean()
        if self.wallet_id and self.wallet.partner_group_id != self.partner_group_id:
            raise ValidationError(
                {"wallet": "Le wallet doit appartenir au groupe de la transaction."}
            )
        if self.amount <= Decimal("0.00"):
            raise ValidationError({"amount": "Le montant doit etre strictement positif."})


class Payment(models.Model):
    class Method(models.TextChoices):
        WAVE = "WAVE", "Wave"
        ORANGE_MONEY = "ORANGE_MONEY", "Orange Money"
        WALLET = "WALLET", "Wallet"

    class Status(models.TextChoices):
        PENDING = "PENDING", "En attente"
        CONFIRMED = "CONFIRMED", "Confirme"
        FAILED = "FAILED", "Echoue"
        CANCELLED = "CANCELLED", "Annule"

    partner_group = models.ForeignKey(
        "groups.PartnerGroup",
        on_delete=models.PROTECT,
        related_name="payments",
    )
    quote = models.ForeignKey(
        "quotes.Quote",
        on_delete=models.PROTECT,
        related_name="payments",
    )
    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.PROTECT,
        related_name="payments",
    )
    contributor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="payments",
        null=True,
        blank=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="created_payments",
        null=True,
        blank=True,
    )
    method = models.CharField(max_length=20, choices=Method.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=3, default="XOF")
    external_reference = models.CharField(max_length=120, blank=True)
    idempotency_key = models.CharField(max_length=120, blank=True)
    wallet_transaction = models.ForeignKey(
        WalletTransaction,
        on_delete=models.PROTECT,
        related_name="payments",
        null=True,
        blank=True,
    )
    confirmed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(
                fields=["partner_group", "idempotency_key"],
                condition=~Q(idempotency_key=""),
                name="payments_unique_idempotency_per_group",
            )
        ]

    def __str__(self) -> str:
        return f"Payment {self.id} - {self.status}"

    def clean(self):
        super().clean()

        if self.amount <= Decimal("0.00"):
            raise ValidationError({"amount": "Le montant doit etre strictement positif."})

        if self.quote_id and self.quote.partner_group_id != self.partner_group_id:
            raise ValidationError(
                {"quote": "Le devis doit appartenir au groupe du paiement."}
            )

        if self.client_id and self.client.partner_group_id != self.partner_group_id:
            raise ValidationError(
                {"client": "Le client doit appartenir au groupe du paiement."}
            )

        if self.quote_id and self.client_id and self.quote.client_id != self.client_id:
            raise ValidationError(
                {"client": "Le client doit etre celui du devis paye."}
            )

        if self.contributor_id:
            if not self.contributor.is_contributor:
                raise ValidationError({"contributor": "Le contributeur doit etre un apporteur."})
            if self.contributor.partner_group_id != self.partner_group_id:
                raise ValidationError(
                    {"contributor": "L'apporteur doit appartenir au groupe du paiement."}
                )

        if self.quote_id and self.quote.contributor_id and self.contributor_id:
            if self.quote.contributor_id != self.contributor_id:
                raise ValidationError(
                    {"contributor": "L'apporteur doit etre celui du devis paye."}
                )

        if self.created_by_id and not self.created_by.is_general_admin:
            if self.created_by.partner_group_id != self.partner_group_id:
                raise ValidationError(
                    {"created_by": "Le createur doit appartenir au groupe du paiement."}
                )


class PaymentWebhookEvent(models.Model):
    class Provider(models.TextChoices):
        WAVE = "WAVE", "Wave"
        ORANGE_MONEY = "ORANGE_MONEY", "Orange Money"

    class Status(models.TextChoices):
        RECEIVED = "RECEIVED", "Recu"
        PROCESSED = "PROCESSED", "Traite"
        IGNORED = "IGNORED", "Ignore"
        FAILED = "FAILED", "Echoue"

    provider = models.CharField(max_length=20, choices=Provider.choices)
    event_id = models.CharField(max_length=160)
    event_type = models.CharField(max_length=120, blank=True)
    provider_reference = models.CharField(max_length=160, blank=True)
    payment = models.ForeignKey(
        Payment,
        on_delete=models.SET_NULL,
        related_name="webhook_events",
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.RECEIVED,
    )
    payload = models.JSONField(default=dict, blank=True)
    headers = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    received_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-received_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "event_id"],
                name="payment_webhook_unique_event_per_provider",
            )
        ]

    def __str__(self) -> str:
        return f"{self.provider} {self.event_id} - {self.status}"

    def save(self, *args, **kwargs):
        self.payload = sanitize_value(self.payload or {})
        self.headers = sanitize_value(self.headers or {})
        self.error_message = sanitize_error_message(self.error_message)
        super().save(*args, **kwargs)
