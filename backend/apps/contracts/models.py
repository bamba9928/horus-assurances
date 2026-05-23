from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Contract(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Brouillon"
        READY_TO_ISSUE = "READY_TO_ISSUE", "Pret a emettre"
        ISSUED = "ISSUED", "Emis"
        CANCELLED = "CANCELLED", "Annule"

    partner_group = models.ForeignKey(
        "groups.PartnerGroup",
        on_delete=models.PROTECT,
        related_name="contracts",
    )
    quote = models.OneToOneField(
        "quotes.Quote",
        on_delete=models.PROTECT,
        related_name="contract",
    )
    payment = models.OneToOneField(
        "payments.Payment",
        on_delete=models.PROTECT,
        related_name="contract",
    )
    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.PROTECT,
        related_name="contracts",
    )
    vehicle = models.ForeignKey(
        "vehicles.Vehicle",
        on_delete=models.PROTECT,
        related_name="contracts",
    )
    contributor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="contracts",
        null=True,
        blank=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="created_contracts",
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.READY_TO_ISSUE,
    )
    contract_number = models.CharField(max_length=80, unique=True, null=True, blank=True)
    attestation_reference = models.CharField(
        max_length=120,
        unique=True,
        null=True,
        blank=True,
    )
    qr_code_reference = models.CharField(max_length=120, unique=True, null=True, blank=True)
    attestation_url = models.URLField(max_length=500, blank=True)
    carte_brune_url = models.URLField(max_length=500, blank=True)
    issued_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return self.contract_number or f"Contract {self.id}"

    def clean(self):
        super().clean()

        if self.payment_id and self.payment.status != "CONFIRMED":
            raise ValidationError(
                {"payment": "Le paiement doit etre confirme avant de creer un contrat."}
            )

        if self.quote_id and self.quote.partner_group_id != self.partner_group_id:
            raise ValidationError(
                {"quote": "Le devis doit appartenir au groupe du contrat."}
            )

        if self.payment_id and self.payment.partner_group_id != self.partner_group_id:
            raise ValidationError(
                {"payment": "Le paiement doit appartenir au groupe du contrat."}
            )

        if self.client_id and self.client.partner_group_id != self.partner_group_id:
            raise ValidationError(
                {"client": "Le client doit appartenir au groupe du contrat."}
            )

        if self.vehicle_id and self.vehicle.partner_group_id != self.partner_group_id:
            raise ValidationError(
                {"vehicle": "Le vehicule doit appartenir au groupe du contrat."}
            )

        if self.quote_id and self.payment_id and self.payment.quote_id != self.quote_id:
            raise ValidationError(
                {"payment": "Le paiement doit etre rattache au devis du contrat."}
            )

        if self.quote_id and self.client_id and self.quote.client_id != self.client_id:
            raise ValidationError(
                {"client": "Le client doit etre celui du devis."}
            )

        if self.quote_id and self.vehicle_id and self.quote.vehicle_id != self.vehicle_id:
            raise ValidationError(
                {"vehicle": "Le vehicule doit etre celui du devis."}
            )

        if self.contributor_id:
            if not self.contributor.is_contributor:
                raise ValidationError({"contributor": "Le contributeur doit etre un apporteur."})
            if self.contributor.partner_group_id != self.partner_group_id:
                raise ValidationError(
                    {"contributor": "L'apporteur doit appartenir au groupe du contrat."}
                )

        if self.quote_id and self.quote.contributor_id and self.contributor_id:
            if self.quote.contributor_id != self.contributor_id:
                raise ValidationError(
                    {"contributor": "L'apporteur doit etre celui du devis."}
                )

        if self.created_by_id and not self.created_by.is_general_admin:
            if self.created_by.partner_group_id != self.partner_group_id:
                raise ValidationError(
                    {"created_by": "Le createur doit appartenir au groupe du contrat."}
                )
