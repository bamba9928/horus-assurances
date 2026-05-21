from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.payments.models import Payment

from .models import Contract

User = get_user_model()


class ContractSerializer(serializers.ModelSerializer):
    partner_group_name = serializers.CharField(source="partner_group.name", read_only=True)
    quote_reference = serializers.UUIDField(source="quote.reference", read_only=True)
    client_display_name = serializers.CharField(source="client.display_name", read_only=True)
    vehicle_registration_number = serializers.CharField(
        source="vehicle.registration_number",
        read_only=True,
    )
    contributor_username = serializers.CharField(source="contributor.username", read_only=True)

    class Meta:
        model = Contract
        fields = [
            "id",
            "partner_group",
            "partner_group_name",
            "quote",
            "quote_reference",
            "payment",
            "client",
            "client_display_name",
            "vehicle",
            "vehicle_registration_number",
            "contributor",
            "contributor_username",
            "created_by",
            "status",
            "contract_number",
            "attestation_reference",
            "qr_code_reference",
            "issued_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_by",
            "contract_number",
            "attestation_reference",
            "qr_code_reference",
            "issued_at",
            "created_at",
            "updated_at",
        ]
        validators = []
        extra_kwargs = {
            "partner_group": {"required": False},
            "quote": {"required": False},
            "client": {"required": False},
            "vehicle": {"required": False},
            "contributor": {"required": False, "allow_null": True},
            "status": {"read_only": True},
        }

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        instance = self.instance

        payment = attrs.get("payment", getattr(instance, "payment", None))
        partner_group = attrs.get(
            "partner_group", getattr(instance, "partner_group", None)
        )
        quote = attrs.get("quote", getattr(instance, "quote", None))
        client = attrs.get("client", getattr(instance, "client", None))
        vehicle = attrs.get("vehicle", getattr(instance, "vehicle", None))
        contributor = attrs.get("contributor", getattr(instance, "contributor", None))

        if not user or not user.is_authenticated:
            raise serializers.ValidationError("Authentification obligatoire.")
        if payment is None:
            raise serializers.ValidationError({"payment": "Le paiement est obligatoire."})
        if payment.status != Payment.Status.CONFIRMED:
            raise serializers.ValidationError(
                {"payment": "Un paiement confirme est obligatoire."}
            )

        expected_group = payment.partner_group
        expected_quote = payment.quote
        expected_client = payment.client
        expected_vehicle = payment.quote.vehicle
        expected_contributor = payment.contributor or payment.quote.contributor

        if partner_group and partner_group != expected_group:
            raise serializers.ValidationError(
                {"partner_group": "Le groupe doit etre celui du paiement."}
            )
        if quote and quote != expected_quote:
            raise serializers.ValidationError(
                {"quote": "Le devis doit etre celui du paiement."}
            )
        if client and client != expected_client:
            raise serializers.ValidationError(
                {"client": "Le client doit etre celui du paiement."}
            )
        if vehicle and vehicle != expected_vehicle:
            raise serializers.ValidationError(
                {"vehicle": "Le vehicule doit etre celui du devis paye."}
            )

        if user.is_general_admin:
            pass
        elif user.is_group_admin:
            if expected_group != user.partner_group:
                raise serializers.ValidationError(
                    {"partner_group": "Un admin de groupe ne peut utiliser que son groupe."}
                )
        elif user.is_contributor:
            if expected_group != user.partner_group:
                raise serializers.ValidationError(
                    {"partner_group": "Un apporteur ne peut utiliser que son groupe."}
                )
            if expected_contributor and expected_contributor != user:
                raise serializers.ValidationError(
                    {"contributor": "Un apporteur ne peut creer que ses propres contrats."}
                )
            contributor = user
        else:
            raise serializers.ValidationError("Role utilisateur non autorise.")

        if expected_contributor:
            if contributor and contributor != expected_contributor:
                raise serializers.ValidationError(
                    {"contributor": "L'apporteur doit etre celui du paiement."}
                )
            contributor = expected_contributor

        if contributor:
            if contributor.role != User.Role.CONTRIBUTOR:
                raise serializers.ValidationError(
                    {"contributor": "Le contributeur doit etre un apporteur."}
                )
            if contributor.partner_group_id != expected_group.id:
                raise serializers.ValidationError(
                    {"contributor": "L'apporteur doit appartenir au groupe du contrat."}
                )

        duplicate_quote = Contract.objects.filter(quote=expected_quote)
        duplicate_payment = Contract.objects.filter(payment=payment)
        if instance:
            duplicate_quote = duplicate_quote.exclude(pk=instance.pk)
            duplicate_payment = duplicate_payment.exclude(pk=instance.pk)
        if duplicate_quote.exists():
            raise serializers.ValidationError(
                {"quote": "Ce devis a deja un contrat."}
            )
        if duplicate_payment.exists():
            raise serializers.ValidationError(
                {"payment": "Ce paiement a deja un contrat."}
            )

        attrs["partner_group"] = expected_group
        attrs["quote"] = expected_quote
        attrs["client"] = expected_client
        attrs["vehicle"] = expected_vehicle
        attrs["contributor"] = contributor
        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        contract = Contract(**validated_data)
        contract.created_by = request.user
        contract.status = Contract.Status.READY_TO_ISSUE
        contract.full_clean()
        contract.save()
        return contract

    def update(self, instance, validated_data):
        if instance.status == Contract.Status.ISSUED:
            raise serializers.ValidationError(
                {"status": "Un contrat emis ne peut plus etre modifie."}
            )
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.full_clean()
        instance.save()
        return instance


class ContractFromPaymentSerializer(serializers.Serializer):
    payment = serializers.PrimaryKeyRelatedField(queryset=Payment.objects.all())
