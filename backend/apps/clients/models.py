from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone


class Client(models.Model):
    class ClientType(models.TextChoices):
        INDIVIDUAL = "INDIVIDUAL", "Personne physique"
        COMPANY = "COMPANY", "Personne morale"

    partner_group = models.ForeignKey(
        "groups.PartnerGroup",
        on_delete=models.PROTECT,
        related_name="clients",
    )
    contributor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="clients",
        null=True,
        blank=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="created_clients",
        null=True,
        blank=True,
    )
    client_type = models.CharField(
        max_length=20,
        choices=ClientType.choices,
        default=ClientType.INDIVIDUAL,
    )
    first_name = models.CharField(max_length=120, blank=True)
    last_name = models.CharField(max_length=120, blank=True)
    company_name = models.CharField(max_length=180, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=32)
    address = models.CharField(max_length=255, blank=True)
    identity_number = models.CharField(max_length=80, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(
                fields=["partner_group", "phone"],
                name="clients_unique_phone_per_group",
            ),
            models.CheckConstraint(
                condition=(
                    Q(client_type="INDIVIDUAL")
                    & (Q(first_name__gt="") | Q(last_name__gt=""))
                )
                | (Q(client_type="COMPANY") & Q(company_name__gt="")),
                name="clients_required_display_name",
            ),
        ]

    def __str__(self) -> str:
        return self.display_name

    @property
    def display_name(self) -> str:
        if self.client_type == self.ClientType.COMPANY:
            return self.company_name
        return f"{self.first_name} {self.last_name}".strip()

    def clean(self):
        super().clean()
        if self.client_type == self.ClientType.COMPANY and not self.company_name:
            raise ValidationError({"company_name": "Le nom de la societe est obligatoire."})
        if self.client_type == self.ClientType.INDIVIDUAL and not (
            self.first_name or self.last_name
        ):
            raise ValidationError(
                {"first_name": "Un client physique doit avoir un prenom ou un nom."}
            )

        if self.contributor_id:
            if not self.contributor.is_contributor:
                raise ValidationError({"contributor": "Le contributeur doit etre un apporteur."})
            if self.contributor.partner_group_id != self.partner_group_id:
                raise ValidationError(
                    {"contributor": "L'apporteur doit appartenir au groupe du client."}
                )

        if self.created_by_id and not self.created_by.is_general_admin:
            if self.created_by.partner_group_id != self.partner_group_id:
                raise ValidationError(
                    {"created_by": "Le createur doit appartenir au groupe du client."}
                )


class ClientAccessToken(models.Model):
    class DeliveryChannel(models.TextChoices):
        SMS = "SMS", "SMS"
        EMAIL = "EMAIL", "Email"
        MANUAL = "MANUAL", "Manuel"

    partner_group = models.ForeignKey(
        "groups.PartnerGroup",
        on_delete=models.PROTECT,
        related_name="client_access_tokens",
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="access_tokens",
    )
    contract = models.ForeignKey(
        "contracts.Contract",
        on_delete=models.CASCADE,
        related_name="client_access_tokens",
    )
    token_hash = models.CharField(max_length=64, unique=True)
    delivery_channel = models.CharField(
        max_length=20,
        choices=DeliveryChannel.choices,
        default=DeliveryChannel.MANUAL,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="created_client_access_tokens",
        null=True,
        blank=True,
    )
    rotated_from = models.OneToOneField(
        "self",
        on_delete=models.SET_NULL,
        related_name="rotated_to",
        null=True,
        blank=True,
    )
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        return f"Client access token {self.client_id}/{self.contract_id}"

    @property
    def is_active(self) -> bool:
        return (
            self.revoked_at is None
            and self.expires_at > timezone.now()
            and self.client.is_active
        )

    def clean(self):
        super().clean()
        if self.client_id and self.partner_group_id:
            if self.client.partner_group_id != self.partner_group_id:
                raise ValidationError(
                    {"client": "Le client doit appartenir au groupe du jeton."}
                )
        if self.contract_id and self.partner_group_id:
            if self.contract.partner_group_id != self.partner_group_id:
                raise ValidationError(
                    {"contract": "Le contrat doit appartenir au groupe du jeton."}
                )
        if self.client_id and self.contract_id:
            if self.contract.client_id != self.client_id:
                raise ValidationError(
                    {"contract": "Le contrat doit appartenir au client du jeton."}
                )
        if self.client_id and not self.client.is_active and self.revoked_at is None:
            raise ValidationError({"client": "Le client doit etre actif."})
