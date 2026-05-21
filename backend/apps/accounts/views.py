from django.contrib.auth import get_user_model
from rest_framework import viewsets

from .permissions import UserAccessPermission
from .serializers import UserSerializer

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [UserAccessPermission]
    filterset_fields = ["role", "partner_group", "is_active"]
    search_fields = ["username", "email", "first_name", "last_name", "phone"]
    ordering_fields = ["id", "username", "created_at"]
    ordering = ["id"]

    def get_queryset(self):
        user = self.request.user
        queryset = User.objects.select_related("partner_group").all()

        if user.is_general_admin:
            return queryset
        if user.is_group_admin:
            return queryset.filter(partner_group=user.partner_group)
        if user.is_contributor:
            return queryset.filter(id=user.id)
        return queryset.none()
