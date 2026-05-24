from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from apps.ass_api.sanitizers import sanitize_value


class Notification(models.Model):
    class Type(models.TextChoices):
        PAYMENT_CONFIRMED = "PAYMENT_CONFIRMED", "Paiement confirme"
        CONTRACT_ISSUED = "CONTRACT_ISSUED", "Contrat emis"
        COMMISSION_GENERATED = "COMMISSION_GENERATED", "Commission generee"
        COMMISSION_PAID = "COMMISSION_PAID", "Commission payee"

    partner_group = models.ForeignKey(
        "groups.PartnerGroup",
        on_delete=models.PROTECT,
        related_name="notifications",
        null=True,
        blank=True,
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True,
    )
    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True,
    )
    notification_type = models.CharField(max_length=40, choices=Type.choices)
    title = models.CharField(max_length=160)
    message = models.TextField(blank=True)
    target_type = models.CharField(max_length=120, blank=True)
    target_id = models.CharField(max_length=64, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(recipient__isnull=False) | Q(client__isnull=False),
                name="notifications_recipient_or_client_required",
            )
        ]

    def __str__(self) -> str:
        target = self.recipient or self.client
        return f"{self.notification_type} -> {target}"

    @property
    def is_read(self) -> bool:
        return self.read_at is not None

    def save(self, *args, **kwargs):
        self.metadata = sanitize_value(self.metadata or {})
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.recipient_id is None and self.client_id is None:
            raise ValidationError(
                {"recipient": "Une notification doit cibler un utilisateur ou un client."}
            )
        if self.client_id and self.partner_group_id:
            if self.client.partner_group_id != self.partner_group_id:
                raise ValidationError(
                    {"client": "Le client doit appartenir au groupe de la notification."}
                )
