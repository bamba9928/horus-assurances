from django.db import models

from .sanitizers import sanitize_error_message, sanitize_value


class ASSAPICallLog(models.Model):
    class Status(models.TextChoices):
        SUCCESS = "SUCCESS", "Succes"
        ERROR = "ERROR", "Erreur"

    partner_group = models.ForeignKey(
        "groups.PartnerGroup",
        on_delete=models.PROTECT,
        related_name="ass_api_logs",
        null=True,
        blank=True,
    )
    contract = models.ForeignKey(
        "contracts.Contract",
        on_delete=models.SET_NULL,
        related_name="ass_api_logs",
        null=True,
        blank=True,
    )
    endpoint = models.CharField(max_length=255)
    method = models.CharField(max_length=10, default="POST")
    status = models.CharField(max_length=20, choices=Status.choices)
    http_status_code = models.PositiveSmallIntegerField(null=True, blank=True)
    request_payload = models.JSONField(default=dict, blank=True)
    response_payload = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    duration_ms = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        return f"{self.method} {self.endpoint} - {self.status}"

    def save(self, *args, **kwargs):
        self.request_payload = sanitize_value(self.request_payload or {})
        self.response_payload = sanitize_value(self.response_payload or {})
        self.error_message = sanitize_error_message(self.error_message)
        super().save(*args, **kwargs)
