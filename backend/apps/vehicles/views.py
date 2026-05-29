from rest_framework import viewsets

from .models import Vehicle
from .serializers import VehicleSerializer


class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.none()
    serializer_class = VehicleSerializer
    filterset_fields = [
        "partner_group",
        "client",
        "contributor",
        "energy",
        "brand_reference",
        "genre_reference",
        "energy_reference",
        "is_active",
    ]
    search_fields = [
        "registration_number",
        "brand",
        "model",
        "chassis_number",
        "genre",
    ]
    ordering_fields = ["id", "created_at", "updated_at"]
    ordering = ["id"]

    def get_queryset(self):
        user = self.request.user
        queryset = Vehicle.objects.select_related(
            "partner_group",
            "client",
            "contributor",
            "created_by",
            "brand_reference",
            "genre_reference",
            "energy_reference",
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
