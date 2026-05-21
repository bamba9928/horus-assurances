from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Vehicle(models.Model):
    class Energy(models.TextChoices):
        GASOLINE = "ESSENCE", "Essence"
        DIESEL = "DIESEL", "Diesel"
        ELECTRIC = "ELECTRIQUE", "Electrique"
        HYBRID = "HYBRIDE", "Hybride"

    partner_group = models.ForeignKey(
        "groups.PartnerGroup",
        on_delete=models.PROTECT,
        related_name="vehicles",
    )
    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.PROTECT,
        related_name="vehicles",
    )
    contributor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="vehicles",
        null=True,
        blank=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="created_vehicles",
        null=True,
        blank=True,
    )
    registration_number = models.CharField(max_length=40)
    brand = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    chassis_number = models.CharField(max_length=100, blank=True)
    genre = models.CharField(max_length=40)
    energy = models.CharField(max_length=20, choices=Energy.choices)
    fiscal_power = models.PositiveSmallIntegerField(null=True, blank=True)
    seats = models.PositiveSmallIntegerField(null=True, blank=True)
    first_registration_date = models.DateField(null=True, blank=True)
    new_value = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    current_value = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(
                fields=["partner_group", "registration_number"],
                name="vehicles_unique_registration_per_group",
            )
        ]

    def __str__(self) -> str:
        return f"{self.registration_number} - {self.brand} {self.model}"

    def clean(self):
        super().clean()
        if self.client_id and self.client.partner_group_id != self.partner_group_id:
            raise ValidationError(
                {"client": "Le client doit appartenir au groupe du vehicule."}
            )

        if self.contributor_id:
            if not self.contributor.is_contributor:
                raise ValidationError({"contributor": "Le contributeur doit etre un apporteur."})
            if self.contributor.partner_group_id != self.partner_group_id:
                raise ValidationError(
                    {"contributor": "L'apporteur doit appartenir au groupe du vehicule."}
                )

        if self.client_id and self.client.contributor_id and self.contributor_id:
            if self.client.contributor_id != self.contributor_id:
                raise ValidationError(
                    {"contributor": "L'apporteur doit etre celui du client rattache."}
                )

        if self.created_by_id and not self.created_by.is_general_admin:
            if self.created_by.partner_group_id != self.partner_group_id:
                raise ValidationError(
                    {"created_by": "Le createur doit appartenir au groupe du vehicule."}
                )
