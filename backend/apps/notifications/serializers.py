from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    partner_group_name = serializers.CharField(source="partner_group.name", read_only=True)
    is_read = serializers.BooleanField(read_only=True)

    class Meta:
        model = Notification
        fields = [
            "id",
            "partner_group",
            "partner_group_name",
            "recipient",
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
