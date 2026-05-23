from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=False)
    partner_group_name = serializers.CharField(source="partner_group.name", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "partner_group",
            "partner_group_name",
            "phone",
            "is_active",
            "password",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        request = self.context.get("request")
        request_user = getattr(request, "user", None)
        instance = self.instance

        role = attrs.get("role", getattr(instance, "role", User.Role.CONTRIBUTOR))
        partner_group = attrs.get(
            "partner_group", getattr(instance, "partner_group", None)
        )

        if request_user and request_user.is_authenticated and request_user.is_group_admin:
            if role != User.Role.CONTRIBUTOR:
                raise serializers.ValidationError(
                    {"role": "Un admin de groupe ne peut gerer que des apporteurs."}
                )
            if partner_group and partner_group != request_user.partner_group:
                raise serializers.ValidationError(
                    {"partner_group": "Le groupe doit etre celui de l'admin connecte."}
                )
            attrs["partner_group"] = request_user.partner_group

        if role == User.Role.GENERAL_ADMIN and partner_group is not None:
            raise serializers.ValidationError(
                {"partner_group": "Un admin general ne doit pas etre rattache a un groupe."}
            )
        if role != User.Role.GENERAL_ADMIN and partner_group is None:
            raise serializers.ValidationError(
                {"partner_group": "Un utilisateur non admin general doit appartenir a un groupe."}
            )

        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.full_clean()
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        if password:
            instance.set_password(password)
        instance.full_clean()
        instance.save()
        return instance


class ContributorSerializer(UserSerializer):
    def validate(self, attrs):
        role = attrs.get("role", getattr(self.instance, "role", User.Role.CONTRIBUTOR))
        if role != User.Role.CONTRIBUTOR:
            raise serializers.ValidationError(
                {"role": "Le endpoint contributors ne gere que les apporteurs."}
            )
        attrs["role"] = User.Role.CONTRIBUTOR
        return super().validate(attrs)
