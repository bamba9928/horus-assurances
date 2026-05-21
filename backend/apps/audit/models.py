from django.conf import settings
from django.db import models

from apps.ass_api.sanitizers import sanitize_value


class AuditLog(models.Model):
    class Action(models.TextChoices):
        WALLET_CREDITED = "WALLET_CREDITED", "Wallet credite"
        WALLET_DEBITED = "WALLET_DEBITED", "Wallet debite"
        PAYMENT_CONFIRMED = "PAYMENT_CONFIRMED", "Paiement confirme"
        CONTRACT_ISSUED = "CONTRACT_ISSUED", "Contrat emis"
        COMMISSION_GENERATED = "COMMISSION_GENERATED", "Commission generee"
        COMMISSION_PAID = "COMMISSION_PAID", "Commission payee"

    partner_group = models.ForeignKey(
        "groups.PartnerGroup",
        on_delete=models.PROTECT,
        related_name="audit_logs",
        null=True,
        blank=True,
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
        null=True,
        blank=True,
    )
    action = models.CharField(max_length=40, choices=Action.choices)
    target_type = models.CharField(max_length=120, blank=True)
    target_id = models.CharField(max_length=64, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        return f"{self.action} {self.target_type}:{self.target_id}"

    def save(self, *args, **kwargs):
        self.metadata = sanitize_value(self.metadata or {})
        super().save(*args, **kwargs)
