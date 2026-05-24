import uuid
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Quote(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Brouillon"
        CALCULATED = "CALCULATED", "Calcule"
        ACCEPTED = "ACCEPTED", "Accepte"
        EXPIRED = "EXPIRED", "Expire"
        CANCELLED = "CANCELLED", "Annule"

    class ProductType(models.TextChoices):
        AUTO = "AUTO", "Automobile"
        MOTO = "MOTO", "Moto"
        FLEET = "FLEET", "Flotte"
        TRAILER = "TRAILER", "Remorque"
        SCHOOL_BUS = "SCHOOL_BUS", "Bus ecole"
        GARAGE = "GARAGE", "Garage"

    class Periodicity(models.TextChoices):
        DAYS = "JOURS", "Jours"
        MONTHS = "MOIS", "Mois"
        YEARS = "ANNEES", "Annees"

    reference = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    partner_group = models.ForeignKey(
        "groups.PartnerGroup",
        on_delete=models.PROTECT,
        related_name="quotes",
    )
    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.PROTECT,
        related_name="quotes",
    )
    vehicle = models.ForeignKey(
        "vehicles.Vehicle",
        on_delete=models.PROTECT,
        related_name="quotes",
    )
    contributor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="quotes",
        null=True,
        blank=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="created_quotes",
        null=True,
        blank=True,
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    product_type = models.CharField(
        max_length=20,
        choices=ProductType.choices,
        default=ProductType.AUTO,
    )
    periodicity = models.CharField(
        max_length=20,
        choices=Periodicity.choices,
        default=Periodicity.MONTHS,
    )
    duration = models.PositiveSmallIntegerField(default=12)
    effective_date = models.DateField(null=True, blank=True)
    expiration_date = models.DateField(null=True, blank=True)
    coverage_options = models.JSONField(default=list, blank=True)
    ass_product_data = models.JSONField(default=dict, blank=True)
    civil_liability_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    premium_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    fees_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    total_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return f"Quote {self.reference}"

    def clean(self):
        super().clean()

        if self.client_id and self.client.partner_group_id != self.partner_group_id:
            raise ValidationError(
                {"client": "Le client doit appartenir au groupe du devis."}
            )

        if self.vehicle_id and self.vehicle.partner_group_id != self.partner_group_id:
            raise ValidationError(
                {"vehicle": "Le vehicule doit appartenir au groupe du devis."}
            )

        if self.client_id and self.vehicle_id and self.vehicle.client_id != self.client_id:
            raise ValidationError(
                {"vehicle": "Le vehicule doit etre rattache au client du devis."}
            )

        if self.ass_product_data is None:
            self.ass_product_data = {}
        if not isinstance(self.ass_product_data, dict):
            raise ValidationError(
                {"ass_product_data": "Les donnees produit ASS doivent etre un objet JSON."}
            )

        if self.contributor_id:
            if not self.contributor.is_contributor:
                raise ValidationError({"contributor": "Le contributeur doit etre un apporteur."})
            if self.contributor.partner_group_id != self.partner_group_id:
                raise ValidationError(
                    {"contributor": "L'apporteur doit appartenir au groupe du devis."}
                )

        expected_contributor_id = None
        if self.client_id and self.client.contributor_id:
            expected_contributor_id = self.client.contributor_id
        if self.vehicle_id and self.vehicle.contributor_id:
            expected_contributor_id = self.vehicle.contributor_id

        if expected_contributor_id and self.contributor_id:
            if self.contributor_id != expected_contributor_id:
                raise ValidationError(
                    {"contributor": "L'apporteur doit etre celui du client et du vehicule."}
                )

        if self.created_by_id and not self.created_by.is_general_admin:
            if self.created_by.partner_group_id != self.partner_group_id:
                raise ValidationError(
                    {"created_by": "Le createur doit appartenir au groupe du devis."}
                )

    def refresh_total_amount(self) -> None:
        self.total_amount = self.premium_amount + self.fees_amount
