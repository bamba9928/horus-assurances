from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.contracts.models import Contract

from .models import Commission, CommissionRule

User = get_user_model()


class CommissionRuleSerializer(serializers.ModelSerializer):
    partner_group_name = serializers.CharField(source="partner_group.name", read_only=True)
    contributor_username = serializers.CharField(source="contributor.username", read_only=True)

    class Meta:
        model = CommissionRule
        fields = [
            "id",
            "partner_group",
            "partner_group_name",
            "contributor",
            "contributor_username",
            "percentage_rate",
            "fixed_amount",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
        validators = []
        extra_kwargs = {
            "partner_group": {"required": False},
            "contributor": {"required": False, "allow_null": True},
        }

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        instance = self.instance

        if not user or not user.is_authenticated:
            raise serializers.ValidationError("Authentification obligatoire.")
        if user.is_contributor:
            raise serializers.ValidationError(
                "Un apporteur ne peut pas modifier les regles de commission."
            )

        partner_group = attrs.get(
            "partner_group", getattr(instance, "partner_group", None)
        )
        contributor = attrs.get("contributor", getattr(instance, "contributor", None))
        is_active = attrs.get("is_active", getattr(instance, "is_active", True))

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
        else:
            raise serializers.ValidationError("Role utilisateur non autorise.")

        if contributor:
            if contributor.role != User.Role.CONTRIBUTOR:
                raise serializers.ValidationError(
                    {"contributor": "Le contributeur doit etre un apporteur."}
                )
            if contributor.partner_group_id != partner_group.id:
                raise serializers.ValidationError(
                    {"contributor": "L'apporteur doit appartenir au groupe de la regle."}
                )

        if is_active:
            duplicate_query = CommissionRule.objects.filter(
                partner_group=partner_group,
                contributor=contributor,
                is_active=True,
            )
            if instance:
                duplicate_query = duplicate_query.exclude(pk=instance.pk)
            if duplicate_query.exists():
                raise serializers.ValidationError(
                    {"is_active": "Une regle active existe deja pour cette cible."}
                )

        return attrs

    def create(self, validated_data):
        rule = CommissionRule(**validated_data)
        rule.full_clean()
        rule.save()
        return rule

    def update(self, instance, validated_data):
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.full_clean()
        instance.save()
        return instance


class CommissionSerializer(serializers.ModelSerializer):
    partner_group_name = serializers.CharField(source="partner_group.name", read_only=True)
    contributor_username = serializers.CharField(source="contributor.username", read_only=True)
    contract_number = serializers.CharField(source="contract.contract_number", read_only=True)

    class Meta:
        model = Commission
        fields = [
            "id",
            "partner_group",
            "partner_group_name",
            "contract",
            "contract_number",
            "payment",
            "contributor",
            "contributor_username",
            "rule",
            "base_amount",
            "percentage_rate",
            "fixed_amount",
            "amount",
            "net_to_pay_amount",
            "status",
            "generated_at",
            "paid_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class CommissionGenerateSerializer(serializers.Serializer):
    contract = serializers.PrimaryKeyRelatedField(queryset=Contract.objects.all())
