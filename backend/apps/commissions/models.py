from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class CommissionRule(models.Model):
    partner_group = models.ForeignKey(
        "groups.PartnerGroup",
        on_delete=models.PROTECT,
        related_name="commission_rules",
    )
    contributor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="commission_rules",
        null=True,
        blank=True,
    )
    percentage_rate = models.DecimalField(
        max_digits=7,
        decimal_places=4,
        default=Decimal("0.0000"),
    )
    fixed_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(
                fields=["partner_group"],
                condition=Q(contributor__isnull=True, is_active=True),
                name="commissions_one_active_group_rule",
            ),
            models.UniqueConstraint(
                fields=["partner_group", "contributor"],
                condition=Q(contributor__isnull=False, is_active=True),
                name="commissions_one_active_contributor_rule",
            ),
        ]

    def __str__(self) -> str:
        target = self.contributor or self.partner_group
        return f"Commission rule {target}"

    def clean(self):
        super().clean()
        if self.percentage_rate < Decimal("0.0000"):
            raise ValidationError(
                {"percentage_rate": "Le pourcentage de commission ne peut pas etre negatif."}
            )
        if self.fixed_amount < Decimal("0.00"):
            raise ValidationError(
                {"fixed_amount": "Le montant fixe de commission ne peut pas etre negatif."}
            )
        if self.contributor_id:
            if not self.contributor.is_contributor:
                raise ValidationError({"contributor": "Le contributeur doit etre un apporteur."})
            if self.contributor.partner_group_id != self.partner_group_id:
                raise ValidationError(
                    {"contributor": "L'apporteur doit appartenir au groupe de la regle."}
                )


class Commission(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "En attente"
        EARNED = "EARNED", "Acquise"
        PAID = "PAID", "Payee"
        CANCELLED = "CANCELLED", "Annulee"

    partner_group = models.ForeignKey(
        "groups.PartnerGroup",
        on_delete=models.PROTECT,
        related_name="commissions",
    )
    contract = models.OneToOneField(
        "contracts.Contract",
        on_delete=models.PROTECT,
        related_name="commission",
    )
    payment = models.ForeignKey(
        "payments.Payment",
        on_delete=models.PROTECT,
        related_name="commissions",
    )
    contributor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="commissions",
    )
    rule = models.ForeignKey(
        CommissionRule,
        on_delete=models.SET_NULL,
        related_name="commissions",
        null=True,
        blank=True,
    )
    base_amount = models.DecimalField(max_digits=14, decimal_places=2)
    percentage_rate = models.DecimalField(max_digits=7, decimal_places=4)
    fixed_amount = models.DecimalField(max_digits=14, decimal_places=2)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    net_to_pay_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.EARNED)
    generated_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return f"Commission {self.amount} for {self.contributor}"

    def clean(self):
        super().clean()
        if self.contract_id and self.contract.partner_group_id != self.partner_group_id:
            raise ValidationError(
                {"contract": "Le contrat doit appartenir au groupe de la commission."}
            )
        if self.payment_id and self.payment.partner_group_id != self.partner_group_id:
            raise ValidationError(
                {"payment": "Le paiement doit appartenir au groupe de la commission."}
            )
        if self.contract_id and self.payment_id and self.contract.payment_id != self.payment_id:
            raise ValidationError(
                {"payment": "Le paiement doit etre celui du contrat."}
            )
        if self.contributor_id:
            if not self.contributor.is_contributor:
                raise ValidationError({"contributor": "Le contributeur doit etre un apporteur."})
            if self.contributor.partner_group_id != self.partner_group_id:
                raise ValidationError(
                    {"contributor": "L'apporteur doit appartenir au groupe de la commission."}
                )
        if self.rule_id and self.rule.partner_group_id != self.partner_group_id:
            raise ValidationError(
                {"rule": "La regle doit appartenir au groupe de la commission."}
            )
        if self.base_amount < Decimal("0.00"):
            raise ValidationError({"base_amount": "La base de calcul ne peut pas etre negative."})
        if self.percentage_rate < Decimal("0.0000"):
            raise ValidationError(
                {"percentage_rate": "Le pourcentage ne peut pas etre negatif."}
            )
        if self.fixed_amount < Decimal("0.00"):
            raise ValidationError({"fixed_amount": "Le montant fixe ne peut pas etre negatif."})
        if self.amount < Decimal("0.00"):
            raise ValidationError({"amount": "La commission ne peut pas etre negative."})
        if self.net_to_pay_amount < Decimal("0.00"):
            raise ValidationError(
                {"net_to_pay_amount": "Le net a verser ne peut pas etre negatif."}
            )
        if self.fixed_amount > self.contract.quote.fees_amount:
            raise ValidationError(
                {"fixed_amount": "Le fixe commission ne peut pas depasser les frais ASS."}
            )
        if self.amount > self.payment.amount:
            raise ValidationError(
                {"amount": "La commission ne peut pas depasser le TTC ASS encaisse."}
            )
        expected_net_to_pay = self.payment.amount - self.amount
        if self.net_to_pay_amount != expected_net_to_pay:
            raise ValidationError(
                {"net_to_pay_amount": "Le net a verser doit etre TTC ASS moins commission."}
            )
