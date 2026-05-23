from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Notification
from .serializers import NotificationSerializer


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Notification.objects.none()
    serializer_class = NotificationSerializer
    filterset_fields = ["notification_type", "partner_group", "read_at"]
    ordering_fields = ["id", "created_at", "read_at"]
    ordering = ["-created_at", "-id"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Notification.objects.none()
        if not self.request.user or not self.request.user.is_authenticated:
            return Notification.objects.none()
        return Notification.objects.select_related("partner_group", "recipient").filter(
            recipient=self.request.user
        )

    @action(detail=True, methods=["post"], url_path="mark-read")
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        if notification.read_at is None:
            notification.read_at = timezone.now()
            notification.save(update_fields=["read_at"])
        return Response(NotificationSerializer(notification, context={"request": request}).data)

    @action(detail=False, methods=["post"], url_path="mark-all-read")
    def mark_all_read(self, request):
        now = timezone.now()
        updated_count = self.get_queryset().filter(read_at__isnull=True).update(read_at=now)
        return Response({"marked_read": updated_count}, status=status.HTTP_200_OK)
