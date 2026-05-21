from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from apps.payments.models import Payment

from .models import Contract


@transaction.atomic
def create_contract_from_payment(*, payment, created_by=None):
    payment = (
        Payment.objects.select_for_update()
        .select_related("partner_group", "quote", "client", "contributor")
        .get(pk=payment.pk)
    )

    if payment.status != Payment.Status.CONFIRMED:
        raise serializers.ValidationError(
            {"payment": "Aucun contrat ne peut etre cree sans paiement confirme."}
        )

    existing_contract = Contract.objects.filter(quote=payment.quote).first()
    if existing_contract:
        return existing_contract

    contract = Contract(
        partner_group=payment.partner_group,
        quote=payment.quote,
        payment=payment,
        client=payment.client,
        vehicle=payment.quote.vehicle,
        contributor=payment.contributor,
        created_by=created_by,
        status=Contract.Status.READY_TO_ISSUE,
    )
    contract.full_clean()
    contract.save()
    return contract


@transaction.atomic
def issue_contract(*, contract):
    contract = (
        Contract.objects.select_for_update()
        .select_related("payment", "quote", "partner_group")
        .get(pk=contract.pk)
    )

    if contract.status == Contract.Status.ISSUED:
        return contract

    if contract.payment.status != Payment.Status.CONFIRMED:
        raise serializers.ValidationError(
            {"payment": "Aucune attestation ne peut etre generee sans paiement confirme."}
        )

    if contract.status == Contract.Status.CANCELLED:
        raise serializers.ValidationError(
            {"status": "Un contrat annule ne peut pas etre emis."}
        )

    if not contract.contract_number:
        contract.contract_number = f"HORUS-{timezone.now().year}-{contract.id:06d}"
    if not contract.attestation_reference:
        contract.attestation_reference = f"LOCAL-ATT-{contract.id:06d}"
    if not contract.qr_code_reference:
        contract.qr_code_reference = f"LOCAL-QR-{contract.id:06d}"

    contract.status = Contract.Status.ISSUED
    contract.issued_at = timezone.now()
    contract.full_clean()
    contract.save(
        update_fields=[
            "contract_number",
            "attestation_reference",
            "qr_code_reference",
            "status",
            "issued_at",
            "updated_at",
        ]
    )
    return contract
