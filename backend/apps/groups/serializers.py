from rest_framework import serializers

from .models import PartnerGroup


class PartnerGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartnerGroup
        fields = ["id", "name", "slug", "status", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
