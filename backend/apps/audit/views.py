from rest_framework.permissions import BasePermission
from rest_framework import viewsets

from .models import AuditLog
from .serializers import AuditLogSerializer


class CanReadAuditLogs(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (user.is_general_admin or user.is_group_admin)
        )


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.none()
    serializer_class = AuditLogSerializer
    permission_classes = [CanReadAuditLogs]
    filterset_fields = ["partner_group", "actor", "action", "target_type", "target_id"]
    ordering_fields = ["id", "created_at"]
    ordering = ["-created_at", "-id"]

    def get_queryset(self):
        user = self.request.user
        queryset = AuditLog.objects.select_related("partner_group", "actor")

        if getattr(self, "swagger_fake_view", False):
            return queryset.none()
        if not user or not user.is_authenticated:
            return queryset.none()
        if user.is_general_admin:
            return queryset
        if user.is_group_admin:
            return queryset.filter(partner_group=user.partner_group)
        return queryset.none()
