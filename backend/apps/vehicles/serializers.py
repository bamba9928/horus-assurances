from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Vehicle

User = get_user_model()


class VehicleSerializer(serializers.ModelSerializer):
    partner_group_name = serializers.CharField(source="partner_group.name", read_only=True)
    client_display_name = serializers.CharField(source="client.display_name", read_only=True)
    contributor_username = serializers.CharField(source="contributor.username", read_only=True)

    class Meta:
        model = Vehicle
        fields = [
            "id",
            "partner_group",
            "partner_group_name",
            "client",
            "client_display_name",
            "contributor",
            "contributor_username",
            "created_by",
            "registration_number",
            "brand",
            "model",
            "chassis_number",
            "genre",
            "energy",
            "fiscal_power",
            "seats",
            "first_registration_date",
            "new_value",
            "current_value",
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
        client = attrs.get("client", getattr(instance, "client", None))
        contributor = attrs.get("contributor", getattr(instance, "contributor", None))

        if not user or not user.is_authenticated:
            raise serializers.ValidationError("Authentification obligatoire.")

        if client and partner_group and client.partner_group_id != partner_group.id:
            raise serializers.ValidationError(
                {"client": "Le client doit appartenir au groupe du vehicule."}
            )

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
                    {"contributor": "Un apporteur ne peut creer que ses propres vehicules."}
                )
            partner_group = user.partner_group
            contributor = user
            attrs["partner_group"] = partner_group
            attrs["contributor"] = contributor
        else:
            raise serializers.ValidationError("Role utilisateur non autorise.")

        if client and client.partner_group_id != partner_group.id:
            raise serializers.ValidationError(
                {"client": "Le client doit appartenir au groupe du vehicule."}
            )

        if contributor:
            if contributor.role != User.Role.CONTRIBUTOR:
                raise serializers.ValidationError(
                    {"contributor": "Le contributeur doit etre un apporteur."}
                )
            if contributor.partner_group_id != partner_group.id:
                raise serializers.ValidationError(
                    {"contributor": "L'apporteur doit appartenir au groupe du vehicule."}
                )

        if client and client.contributor_id:
            if contributor is None:
                contributor = client.contributor
                attrs["contributor"] = contributor
            elif contributor != client.contributor:
                raise serializers.ValidationError(
                    {"contributor": "L'apporteur doit etre celui du client rattache."}
                )

        registration_number = attrs.get(
            "registration_number", getattr(instance, "registration_number", None)
        )
        if registration_number and partner_group:
            duplicate_query = Vehicle.objects.filter(
                partner_group=partner_group,
                registration_number=registration_number,
            )
            if instance:
                duplicate_query = duplicate_query.exclude(pk=instance.pk)
            if duplicate_query.exists():
                raise serializers.ValidationError(
                    {
                        "registration_number": (
                            "Un vehicule avec cette immatriculation existe deja dans ce groupe."
                        )
                    }
                )

        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        validated_data["created_by"] = request.user
        vehicle = Vehicle(**validated_data)
        vehicle.full_clean()
        vehicle.save()
        return vehicle

    def update(self, instance, validated_data):
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.full_clean()
        instance.save()
        return instance
