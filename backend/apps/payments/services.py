from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from .models import GroupWallet, Payment, WalletTransaction


def get_or_create_wallet(partner_group):
    wallet, _ = GroupWallet.objects.get_or_create(partner_group=partner_group)
    return wallet


def _normalize_amount(amount) -> Decimal:
    value = Decimal(amount)
    if value <= Decimal("0.00"):
        raise serializers.ValidationError({"amount": "Le montant doit etre positif."})
    return value


@transaction.atomic
def credit_wallet(*, wallet, amount, created_by=None, idempotency_key="", reference=""):
    amount = _normalize_amount(amount)
    wallet = GroupWallet.objects.select_for_update().get(pk=wallet.pk)

    if idempotency_key:
        existing = WalletTransaction.objects.filter(
            partner_group=wallet.partner_group,
            idempotency_key=idempotency_key,
        ).first()
        if existing:
            return existing

    wallet.balance += amount
    wallet.full_clean()
    wallet.save(update_fields=["balance", "updated_at"])

    wallet_transaction = WalletTransaction.objects.create(
        wallet=wallet,
        partner_group=wallet.partner_group,
        transaction_type=WalletTransaction.TransactionType.TOP_UP,
        direction=WalletTransaction.Direction.CREDIT,
        amount=amount,
        balance_after=wallet.balance,
        idempotency_key=idempotency_key,
        reference=reference,
        created_by=created_by,
    )
    wallet_transaction.full_clean()
    return wallet_transaction


@transaction.atomic
def debit_wallet(
    *,
    wallet,
    amount,
    created_by=None,
    idempotency_key="",
    reference="",
    transaction_type=WalletTransaction.TransactionType.DEBIT,
):
    amount = _normalize_amount(amount)
    wallet = GroupWallet.objects.select_for_update().get(pk=wallet.pk)

    if idempotency_key:
        existing = WalletTransaction.objects.filter(
            partner_group=wallet.partner_group,
            idempotency_key=idempotency_key,
        ).first()
        if existing:
            return existing

    if wallet.balance < amount:
        raise serializers.ValidationError({"amount": "Solde wallet insuffisant."})

    wallet.balance -= amount
    wallet.full_clean()
    wallet.save(update_fields=["balance", "updated_at"])

    wallet_transaction = WalletTransaction.objects.create(
        wallet=wallet,
        partner_group=wallet.partner_group,
        transaction_type=transaction_type,
        direction=WalletTransaction.Direction.DEBIT,
        amount=amount,
        balance_after=wallet.balance,
        idempotency_key=idempotency_key,
        reference=reference,
        created_by=created_by,
    )
    wallet_transaction.full_clean()
    return wallet_transaction


@transaction.atomic
def confirm_payment(*, payment, confirmed_by=None, idempotency_key=""):
    payment = Payment.objects.select_for_update().select_related("partner_group").get(
        pk=payment.pk
    )

    if payment.status == Payment.Status.CONFIRMED:
        return payment

    if payment.status != Payment.Status.PENDING:
        raise serializers.ValidationError(
            {"status": "Seul un paiement en attente peut etre confirme."}
        )

    if payment.method == Payment.Method.WALLET:
        wallet = get_or_create_wallet(payment.partner_group)
        wallet_transaction = debit_wallet(
            wallet=wallet,
            amount=payment.amount,
            created_by=confirmed_by,
            idempotency_key=idempotency_key or f"payment-confirm-{payment.pk}",
            reference=f"payment:{payment.pk}",
            transaction_type=WalletTransaction.TransactionType.PAYMENT,
        )
        payment.wallet_transaction = wallet_transaction

    payment.status = Payment.Status.CONFIRMED
    payment.confirmed_at = timezone.now()
    payment.full_clean()
    payment.save(update_fields=["status", "confirmed_at", "wallet_transaction", "updated_at"])
    return payment
