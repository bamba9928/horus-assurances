from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from apps.contracts.models import Contract

from .models import Commission, CommissionRule

MONEY_QUANTIZER = Decimal("0.01")


def calculate_commission_amount(*, base_amount, percentage_rate, fixed_amount):
    percentage_part = (base_amount * percentage_rate / Decimal("100")).quantize(
        MONEY_QUANTIZER,
        rounding=ROUND_HALF_UP,
    )
    return (percentage_part + fixed_amount).quantize(
        MONEY_QUANTIZER,
        rounding=ROUND_HALF_UP,
    )


def get_applicable_commission_rule(*, partner_group, contributor):
    if contributor:
        contributor_rule = CommissionRule.objects.filter(
            partner_group=partner_group,
            contributor=contributor,
            is_active=True,
        ).first()
        if contributor_rule:
            return contributor_rule

    return CommissionRule.objects.filter(
        partner_group=partner_group,
        contributor__isnull=True,
        is_active=True,
    ).first()


@transaction.atomic
def generate_commission_for_contract(*, contract):
    contract = (
        Contract.objects.select_for_update()
        .select_related("partner_group", "payment", "quote", "contributor")
        .get(pk=contract.pk)
    )

    existing_commission = Commission.objects.filter(contract=contract).first()
    if existing_commission:
        return existing_commission

    if contract.status != Contract.Status.ISSUED:
        raise serializers.ValidationError(
            {"contract": "La commission ne peut etre generee que pour un contrat emis."}
        )
    if not contract.contributor_id:
        raise serializers.ValidationError(
            {"contributor": "Le contrat doit etre rattache a un apporteur."}
        )

    rule = get_applicable_commission_rule(
        partner_group=contract.partner_group,
        contributor=contract.contributor,
    )
    percentage_rate = rule.percentage_rate if rule else Decimal("0.0000")
    fixed_amount = rule.fixed_amount if rule else Decimal("0.00")
    if fixed_amount > contract.quote.fees_amount:
        raise serializers.ValidationError(
            {"fixed_amount": "Le fixe commission ne peut pas depasser les frais ASS."}
        )

    base_amount = contract.quote.premium_amount
    amount = calculate_commission_amount(
        base_amount=base_amount,
        percentage_rate=percentage_rate,
        fixed_amount=fixed_amount,
    )
    if amount > contract.payment.amount:
        raise serializers.ValidationError(
            {"amount": "La commission ne peut pas depasser le TTC ASS encaisse."}
        )
    net_to_pay_amount = (contract.payment.amount - amount).quantize(
        MONEY_QUANTIZER,
        rounding=ROUND_HALF_UP,
    )

    commission = Commission.objects.create(
        partner_group=contract.partner_group,
        contract=contract,
        payment=contract.payment,
        contributor=contract.contributor,
        rule=rule,
        base_amount=base_amount,
        percentage_rate=percentage_rate,
        fixed_amount=fixed_amount,
        amount=amount,
        net_to_pay_amount=net_to_pay_amount,
        status=Commission.Status.EARNED,
    )
    commission.full_clean()
    return commission


@transaction.atomic
def mark_commission_paid(*, commission):
    commission = Commission.objects.select_for_update().get(pk=commission.pk)
    if commission.status == Commission.Status.PAID:
        return commission
    if commission.status == Commission.Status.CANCELLED:
        raise serializers.ValidationError(
            {"status": "Une commission annulee ne peut pas etre marquee payee."}
        )
    commission.status = Commission.Status.PAID
    commission.paid_at = timezone.now()
    commission.full_clean()
    commission.save(update_fields=["status", "paid_at", "updated_at"])
    return commission
