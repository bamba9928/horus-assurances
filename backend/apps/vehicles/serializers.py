from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.reference_data.models import EnergyType, VehicleBrand, VehicleGenre

from .models import Vehicle

User = get_user_model()


class VehicleSerializer(serializers.ModelSerializer):
    partner_group_name = serializers.CharField(source="partner_group.name", read_only=True)
    client_display_name = serializers.CharField(source="client.display_name", read_only=True)
    contributor_username = serializers.CharField(source="contributor.username", read_only=True)
    brand_reference = serializers.PrimaryKeyRelatedField(
        queryset=VehicleBrand.objects.active(),
        required=False,
        allow_null=True,
    )
    brand_reference_code = serializers.CharField(
        source="brand_reference.code",
        read_only=True,
        allow_null=True,
    )
    brand_reference_label = serializers.CharField(
        source="brand_reference.label",
        read_only=True,
        allow_null=True,
    )
    genre_reference = serializers.PrimaryKeyRelatedField(
        queryset=VehicleGenre.objects.active(),
        required=False,
        allow_null=True,
    )
    genre_reference_code = serializers.CharField(
        source="genre_reference.code",
        read_only=True,
        allow_null=True,
    )
    genre_reference_label = serializers.CharField(
        source="genre_reference.label",
        read_only=True,
        allow_null=True,
    )
    genre_requires_trailer_section = serializers.BooleanField(
        source="genre_reference.requires_trailer_section",
        read_only=True,
        allow_null=True,
    )
    energy_reference = serializers.PrimaryKeyRelatedField(
        queryset=EnergyType.objects.active(),
        required=False,
        allow_null=True,
    )
    energy_reference_code = serializers.CharField(
        source="energy_reference.code",
        read_only=True,
        allow_null=True,
    )
    energy_reference_label = serializers.CharField(
        source="energy_reference.label",
        read_only=True,
        allow_null=True,
    )

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
            "brand_reference",
            "brand_reference_code",
            "brand_reference_label",
            "model",
            "chassis_number",
            "genre",
            "genre_reference",
            "genre_reference_code",
            "genre_reference_label",
            "genre_requires_trailer_section",
            "energy",
            "energy_reference",
            "energy_reference_code",
            "energy_reference_label",
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
            "brand": {"required": False, "allow_blank": True},
            "genre": {"required": False, "allow_blank": True},
            "energy": {"required": False, "allow_blank": True},
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

        self._fill_legacy_reference_fields(attrs, instance)
        self._validate_required_legacy_fields(attrs, instance)

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

    def _fill_legacy_reference_fields(self, attrs, instance):
        brand_reference = attrs.get(
            "brand_reference", getattr(instance, "brand_reference", None)
        )
        genre_reference = attrs.get(
            "genre_reference", getattr(instance, "genre_reference", None)
        )
        energy_reference = attrs.get(
            "energy_reference", getattr(instance, "energy_reference", None)
        )

        if self._is_missing(attrs.get("brand", getattr(instance, "brand", None))):
            if self._active(brand_reference):
                attrs["brand"] = brand_reference.label

        if self._is_missing(attrs.get("genre", getattr(instance, "genre", None))):
            if self._active(genre_reference):
                attrs["genre"] = genre_reference.ass_code or genre_reference.code

        if self._is_missing(attrs.get("energy", getattr(instance, "energy", None))):
            if self._active(energy_reference):
                attrs["energy"] = energy_reference.ass_code or energy_reference.code

    def _validate_required_legacy_fields(self, attrs, instance):
        errors = {}
        for field_name in ("brand", "genre", "energy"):
            value = attrs.get(field_name, getattr(instance, field_name, None))
            if self._is_missing(value):
                errors[field_name] = "Ce champ est obligatoire si aucune reference active n'est fournie."
        if errors:
            raise serializers.ValidationError(errors)

    @staticmethod
    def _active(reference):
        return reference is not None and reference.is_active

    @staticmethod
    def _is_missing(value):
        return value is None or value == ""

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
