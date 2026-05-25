from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.contracts.models import Contract
from apps.notifications.models import Notification

from .models import Client, ClientAccessToken

User = get_user_model()


class ClientSerializer(serializers.ModelSerializer):
    partner_group_name = serializers.CharField(source="partner_group.name", read_only=True)
    contributor_username = serializers.CharField(source="contributor.username", read_only=True)
    display_name = serializers.CharField(read_only=True)

    class Meta:
        model = Client
        fields = [
            "id",
            "partner_group",
            "partner_group_name",
            "contributor",
            "contributor_username",
            "created_by",
            "client_type",
            "first_name",
            "last_name",
            "company_name",
            "display_name",
            "email",
            "phone",
            "address",
            "identity_number",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]
        validators = []
        extra_kwargs = {
            "partner_group": {"required": False},
            "contributor": {"required": False, "allow_null": True},
        }

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        instance = self.instance

        partner_group = attrs.get(
            "partner_group", getattr(instance, "partner_group", None)
        )
        contributor = attrs.get("contributor", getattr(instance, "contributor", None))

        if not user or not user.is_authenticated:
            raise serializers.ValidationError("Authentification obligatoire.")

        if user.is_general_admin:
            if partner_group is None:
                raise serializers.ValidationError(
                    {"partner_group": "Le groupe est obligatoire."}
                )
        elif user.is_group_admin:
            if partner_group and partner_group != user.partner_group:
                raise serializers.ValidationError(
                    {"partner_group": "Un admin de groupe ne peut utiliser que son groupe."}
                )
            partner_group = user.partner_group
            attrs["partner_group"] = partner_group
        elif user.is_contributor:
            if partner_group and partner_group != user.partner_group:
                raise serializers.ValidationError(
                    {"partner_group": "Un apporteur ne peut utiliser que son groupe."}
                )
            if contributor and contributor != user:
                raise serializers.ValidationError(
                    {"contributor": "Un apporteur ne peut creer que ses propres clients."}
                )
            partner_group = user.partner_group
            contributor = user
            attrs["partner_group"] = partner_group
            attrs["contributor"] = contributor
        else:
            raise serializers.ValidationError("Role utilisateur non autorise.")

        if contributor:
            if contributor.role != User.Role.CONTRIBUTOR:
                raise serializers.ValidationError(
                    {"contributor": "Le contributeur doit etre un apporteur."}
                )
            if contributor.partner_group_id != partner_group.id:
                raise serializers.ValidationError(
                    {"contributor": "L'apporteur doit appartenir au groupe du client."}
                )

        phone = attrs.get("phone", getattr(instance, "phone", None))
        if phone and partner_group:
            duplicate_query = Client.objects.filter(partner_group=partner_group, phone=phone)
            if instance:
                duplicate_query = duplicate_query.exclude(pk=instance.pk)
            if duplicate_query.exists():
                raise serializers.ValidationError(
                    {"phone": "Un client avec ce telephone existe deja dans ce groupe."}
                )

        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        validated_data["created_by"] = request.user
        client = Client(**validated_data)
        client.full_clean()
        client.save()
        return client

    def update(self, instance, validated_data):
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.full_clean()
        instance.save()
        return instance


class ClientAccessTokenSerializer(serializers.ModelSerializer):
    client_display_name = serializers.CharField(source="client.display_name", read_only=True)
    contract_number = serializers.CharField(source="contract.contract_number", read_only=True)
    partner_group_name = serializers.CharField(source="partner_group.name", read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = ClientAccessToken
        fields = [
            "id",
            "partner_group",
            "partner_group_name",
            "client",
            "client_display_name",
            "contract",
            "contract_number",
            "delivery_channel",
            "created_by",
            "rotated_from",
            "expires_at",
            "revoked_at",
            "used_at",
            "is_active",
            "created_at",
        ]
        read_only_fields = fields


class ClientAccessTokenCreateSerializer(serializers.Serializer):
    client = serializers.PrimaryKeyRelatedField(queryset=Client.objects.all())
    contract = serializers.PrimaryKeyRelatedField(queryset=Contract.objects.all())
    delivery_channel = serializers.ChoiceField(
        choices=ClientAccessToken.DeliveryChannel.choices,
        default=ClientAccessToken.DeliveryChannel.MANUAL,
    )
    expires_in_days = serializers.IntegerField(required=False, min_value=1, max_value=365)


class ClientAccessTokenRenewSerializer(serializers.Serializer):
    expires_in_days = serializers.IntegerField(required=False, min_value=1, max_value=365)


class ClientAccessTokenResponseSerializer(serializers.Serializer):
    access_token = serializers.DictField(read_only=True)
    token = serializers.CharField(read_only=True, allow_null=True)
    access_url = serializers.CharField(read_only=True, allow_blank=True)
    mock_delivery = serializers.BooleanField(read_only=True)
    provider = serializers.CharField(read_only=True)
    delivery_channel = serializers.CharField(read_only=True)
    destination = serializers.CharField(read_only=True, allow_blank=True)
    secret_returned = serializers.BooleanField(read_only=True)
    expires_at = serializers.DateTimeField(read_only=True)


class ClientPortalProfileSerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(read_only=True)
    partner_group_name = serializers.CharField(source="partner_group.name", read_only=True)

    class Meta:
        model = Client
        fields = [
            "id",
            "display_name",
            "client_type",
            "first_name",
            "last_name",
            "company_name",
            "email",
            "phone",
            "address",
            "partner_group_name",
        ]
        read_only_fields = fields


class ClientPortalContractSerializer(serializers.ModelSerializer):
    status = serializers.CharField(read_only=True)
    vehicle_registration_number = serializers.CharField(
        source="vehicle.registration_number",
        read_only=True,
    )
    vehicle_brand = serializers.CharField(source="vehicle.brand", read_only=True)
    vehicle_model = serializers.CharField(source="vehicle.model", read_only=True)
    product_type = serializers.CharField(source="quote.product_type", read_only=True)
    total_amount = serializers.DecimalField(
        source="quote.total_amount",
        max_digits=14,
        decimal_places=2,
        read_only=True,
    )
    attestation_available = serializers.SerializerMethodField()
    carte_brune_available = serializers.SerializerMethodField()

    class Meta:
        model = Contract
        fields = [
            "id",
            "status",
            "contract_number",
            "attestation_reference",
            "qr_code_reference",
            "attestation_available",
            "carte_brune_available",
            "issued_at",
            "created_at",
            "vehicle_registration_number",
            "vehicle_brand",
            "vehicle_model",
            "product_type",
            "total_amount",
        ]
        read_only_fields = fields

    def get_attestation_available(self, obj) -> bool:
        return bool(obj.attestation_url)

    def get_carte_brune_available(self, obj) -> bool:
        return bool(obj.carte_brune_url)


class ClientPortalContractDocumentsSerializer(serializers.ModelSerializer):
    attestation_available = serializers.SerializerMethodField()
    carte_brune_available = serializers.SerializerMethodField()
    otp_required = serializers.SerializerMethodField()

    class Meta:
        model = Contract
        fields = [
            "id",
            "status",
            "contract_number",
            "attestation_reference",
            "qr_code_reference",
            "attestation_available",
            "carte_brune_available",
            "otp_required",
            "issued_at",
        ]
        read_only_fields = fields

    def get_attestation_available(self, obj) -> bool:
        return bool(obj.attestation_url)

    def get_carte_brune_available(self, obj) -> bool:
        return bool(obj.carte_brune_url)

    def get_otp_required(self, obj) -> bool:
        return True


class ClientPortalDocumentOtpCreateSerializer(serializers.Serializer):
    document_kind = serializers.ChoiceField(
        choices=[
            ("attestation", "Attestation"),
            ("carte_brune", "Carte brune"),
        ]
    )
    delivery_channel = serializers.ChoiceField(
        choices=ClientAccessToken.DeliveryChannel.choices,
        required=False,
    )


class ClientPortalDocumentOtpResponseSerializer(serializers.Serializer):
    otp = serializers.CharField(read_only=True, allow_null=True)
    document_kind = serializers.CharField(read_only=True)
    mock_delivery = serializers.BooleanField(read_only=True)
    provider = serializers.CharField(read_only=True)
    delivery_channel = serializers.CharField(read_only=True)
    destination = serializers.CharField(read_only=True, allow_blank=True)
    secret_returned = serializers.BooleanField(read_only=True)
    expires_at = serializers.DateTimeField(read_only=True)


class ClientPortalNotificationSerializer(serializers.ModelSerializer):
    is_read = serializers.BooleanField(read_only=True)

    class Meta:
        model = Notification
        fields = [
            "id",
            "notification_type",
            "title",
            "message",
            "target_type",
            "target_id",
            "metadata",
            "is_read",
            "read_at",
            "created_at",
        ]
        read_only_fields = fields
