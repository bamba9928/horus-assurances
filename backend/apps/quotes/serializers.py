from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Quote

User = get_user_model()


class QuoteSerializer(serializers.ModelSerializer):
    partner_group_name = serializers.CharField(source="partner_group.name", read_only=True)
    client_display_name = serializers.CharField(source="client.display_name", read_only=True)
    vehicle_registration_number = serializers.CharField(
        source="vehicle.registration_number",
        read_only=True,
    )
    contributor_username = serializers.CharField(source="contributor.username", read_only=True)

    class Meta:
        model = Quote
        fields = [
            "id",
            "reference",
            "partner_group",
            "partner_group_name",
            "client",
            "client_display_name",
            "vehicle",
            "vehicle_registration_number",
            "contributor",
            "contributor_username",
            "created_by",
            "status",
            "product_type",
            "periodicity",
            "duration",
            "effective_date",
            "expiration_date",
            "coverage_options",
            "civil_liability_amount",
            "premium_amount",
            "fees_amount",
            "total_amount",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "reference", "created_by", "created_at", "updated_at"]
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
        client = attrs.get("client", getattr(instance, "client", None))
        vehicle = attrs.get("vehicle", getattr(instance, "vehicle", None))
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
                    {"contributor": "Un apporteur ne peut creer que ses propres devis."}
                )
            partner_group = user.partner_group
            contributor = user
            attrs["partner_group"] = partner_group
            attrs["contributor"] = contributor
        else:
            raise serializers.ValidationError("Role utilisateur non autorise.")

        if client and client.partner_group_id != partner_group.id:
            raise serializers.ValidationError(
                {"client": "Le client doit appartenir au groupe du devis."}
            )

        if vehicle and vehicle.partner_group_id != partner_group.id:
            raise serializers.ValidationError(
                {"vehicle": "Le vehicule doit appartenir au groupe du devis."}
            )

        if client and vehicle and vehicle.client_id != client.id:
            raise serializers.ValidationError(
                {"vehicle": "Le vehicule doit etre rattache au client du devis."}
            )

        if contributor:
            if contributor.role != User.Role.CONTRIBUTOR:
                raise serializers.ValidationError(
                    {"contributor": "Le contributeur doit etre un apporteur."}
                )
            if contributor.partner_group_id != partner_group.id:
                raise serializers.ValidationError(
                    {"contributor": "L'apporteur doit appartenir au groupe du devis."}
                )

        expected_contributor = None
        if client and client.contributor_id:
            expected_contributor = client.contributor
        if vehicle and vehicle.contributor_id:
            expected_contributor = vehicle.contributor

        if expected_contributor:
            if contributor is None:
                contributor = expected_contributor
                attrs["contributor"] = contributor
            elif contributor != expected_contributor:
                raise serializers.ValidationError(
                    {"contributor": "L'apporteur doit etre celui du client et du vehicule."}
                )

        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        quote = Quote(**validated_data)
        quote.created_by = request.user
        quote.refresh_total_amount()
        quote.full_clean()
        quote.save()
        return quote

    def update(self, instance, validated_data):
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.refresh_total_amount()
        instance.full_clean()
        instance.save()
        return instance


class QuoteCalculateSerializer(serializers.Serializer):
    use_ass = serializers.BooleanField(required=False, default=False)
    rc_discount_amount = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        required=False,
        min_value=0,
        default=0,
    )
    periodicity = serializers.ChoiceField(
        choices=Quote.Periodicity.choices,
        required=False,
    )
    duration = serializers.IntegerField(required=False, min_value=1, max_value=120)
    coverage_options = serializers.JSONField(required=False)
    civil_liability_amount = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        required=False,
        min_value=0,
    )
    premium_amount = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        required=False,
        min_value=0,
    )
    fees_amount = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        required=False,
        min_value=0,
    )
