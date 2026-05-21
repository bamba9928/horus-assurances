from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import GroupWallet, Payment, WalletTransaction

User = get_user_model()


class GroupWalletSerializer(serializers.ModelSerializer):
    partner_group_name = serializers.CharField(source="partner_group.name", read_only=True)

    class Meta:
        model = GroupWallet
        fields = [
            "id",
            "partner_group",
            "partner_group_name",
            "balance",
            "currency",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "balance", "created_at", "updated_at"]


class WalletTransactionSerializer(serializers.ModelSerializer):
    partner_group_name = serializers.CharField(source="partner_group.name", read_only=True)
    created_by_username = serializers.CharField(source="created_by.username", read_only=True)

    class Meta:
        model = WalletTransaction
        fields = [
            "id",
            "wallet",
            "partner_group",
            "partner_group_name",
            "transaction_type",
            "direction",
            "amount",
            "balance_after",
            "idempotency_key",
            "reference",
            "created_by",
            "created_by_username",
            "created_at",
        ]
        read_only_fields = fields


class WalletActionSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=0)
    idempotency_key = serializers.CharField(
        max_length=120,
        required=False,
        allow_blank=True,
    )
    reference = serializers.CharField(max_length=120, required=False, allow_blank=True)


class PaymentSerializer(serializers.ModelSerializer):
    partner_group_name = serializers.CharField(source="partner_group.name", read_only=True)
    client_display_name = serializers.CharField(source="client.display_name", read_only=True)
    quote_reference = serializers.UUIDField(source="quote.reference", read_only=True)
    contributor_username = serializers.CharField(source="contributor.username", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id",
            "partner_group",
            "partner_group_name",
            "quote",
            "quote_reference",
            "client",
            "client_display_name",
            "contributor",
            "contributor_username",
            "created_by",
            "method",
            "status",
            "amount",
            "currency",
            "external_reference",
            "idempotency_key",
            "wallet_transaction",
            "confirmed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_by",
            "wallet_transaction",
            "confirmed_at",
            "created_at",
            "updated_at",
        ]
        validators = []
        extra_kwargs = {
            "partner_group": {"required": False},
            "client": {"required": False},
            "contributor": {"required": False, "allow_null": True},
            "amount": {"required": False},
            "status": {"read_only": True},
        }

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        instance = self.instance

        quote = attrs.get("quote", getattr(instance, "quote", None))
        partner_group = attrs.get(
            "partner_group", getattr(instance, "partner_group", None)
        )
        client = attrs.get("client", getattr(instance, "client", None))
        contributor = attrs.get("contributor", getattr(instance, "contributor", None))
        amount = attrs.get("amount", getattr(instance, "amount", None))

        if not user or not user.is_authenticated:
            raise serializers.ValidationError("Authentification obligatoire.")
        if quote is None:
            raise serializers.ValidationError({"quote": "Le devis est obligatoire."})

        expected_group = quote.partner_group
        expected_client = quote.client
        expected_contributor = quote.contributor

        if partner_group and partner_group != expected_group:
            raise serializers.ValidationError(
                {"partner_group": "Le groupe doit etre celui du devis paye."}
            )
        partner_group = expected_group
        attrs["partner_group"] = partner_group

        if client and client != expected_client:
            raise serializers.ValidationError(
                {"client": "Le client doit etre celui du devis paye."}
            )
        attrs["client"] = expected_client

        if user.is_general_admin:
            pass
        elif user.is_group_admin:
            if partner_group != user.partner_group:
                raise serializers.ValidationError(
                    {"partner_group": "Un admin de groupe ne peut payer que son groupe."}
                )
        elif user.is_contributor:
            if partner_group != user.partner_group:
                raise serializers.ValidationError(
                    {"partner_group": "Un apporteur ne peut payer que son groupe."}
                )
            if expected_contributor and expected_contributor != user:
                raise serializers.ValidationError(
                    {"contributor": "Un apporteur ne peut payer que ses propres devis."}
                )
            if contributor and contributor != user:
                raise serializers.ValidationError(
                    {"contributor": "Un apporteur ne peut creer que ses propres paiements."}
                )
            contributor = user
        else:
            raise serializers.ValidationError("Role utilisateur non autorise.")

        if expected_contributor:
            if contributor and contributor != expected_contributor:
                raise serializers.ValidationError(
                    {"contributor": "L'apporteur doit etre celui du devis paye."}
                )
            contributor = expected_contributor

        if contributor:
            if contributor.role != User.Role.CONTRIBUTOR:
                raise serializers.ValidationError(
                    {"contributor": "Le contributeur doit etre un apporteur."}
                )
            if contributor.partner_group_id != partner_group.id:
                raise serializers.ValidationError(
                    {"contributor": "L'apporteur doit appartenir au groupe du paiement."}
                )
            attrs["contributor"] = contributor

        if amount is None:
            amount = quote.total_amount
            attrs["amount"] = amount
        if amount <= 0:
            raise serializers.ValidationError(
                {"amount": "Le montant doit etre strictement positif."}
            )

        idempotency_key = attrs.get(
            "idempotency_key", getattr(instance, "idempotency_key", "")
        )
        if idempotency_key:
            duplicate_query = Payment.objects.filter(
                partner_group=partner_group,
                idempotency_key=idempotency_key,
            )
            if instance:
                duplicate_query = duplicate_query.exclude(pk=instance.pk)
            if duplicate_query.exists():
                raise serializers.ValidationError(
                    {"idempotency_key": "Cette cle d'idempotence existe deja."}
                )

        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        payment = Payment(**validated_data)
        payment.created_by = request.user
        payment.full_clean()
        payment.save()
        return payment

    def update(self, instance, validated_data):
        if instance.status == Payment.Status.CONFIRMED:
            raise serializers.ValidationError(
                {"status": "Un paiement confirme ne peut plus etre modifie."}
            )
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.full_clean()
        instance.save()
        return instance


class PaymentConfirmSerializer(serializers.Serializer):
    idempotency_key = serializers.CharField(
        max_length=120,
        required=False,
        allow_blank=True,
    )
