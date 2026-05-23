from rest_framework import viewsets

from .models import Client
from .serializers import ClientSerializer


class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.none()
    serializer_class = ClientSerializer
    filterset_fields = ["partner_group", "contributor", "client_type", "is_active"]
    search_fields = [
        "first_name",
        "last_name",
        "company_name",
        "email",
        "phone",
        "identity_number",
    ]
    ordering_fields = ["id", "created_at", "updated_at"]
    ordering = ["id"]

    def get_queryset(self):
        user = self.request.user
        queryset = Client.objects.select_related(
            "partner_group", "contributor", "created_by"
        )

        if getattr(self, "swagger_fake_view", False):
            return queryset.none()
        if not user or not user.is_authenticated:
            return queryset.none()
        if user.is_general_admin:
            return queryset
        if user.is_group_admin:
            return queryset.filter(partner_group=user.partner_group)
        if user.is_contributor:
            return queryset.filter(contributor=user)
        return queryset.none()
