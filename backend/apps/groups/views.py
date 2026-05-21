from rest_framework import viewsets

from apps.accounts.permissions import PartnerGroupAccessPermission

from .models import PartnerGroup
from .serializers import PartnerGroupSerializer


class PartnerGroupViewSet(viewsets.ModelViewSet):
    serializer_class = PartnerGroupSerializer
    permission_classes = [PartnerGroupAccessPermission]
    filterset_fields = ["status"]
    search_fields = ["name", "slug"]
    ordering_fields = ["id", "name", "created_at"]
    ordering = ["name"]

    def get_queryset(self):
        user = self.request.user
        queryset = PartnerGroup.objects.all()

        if user.is_general_admin:
            return queryset
        if user.partner_group_id:
            return queryset.filter(id=user.partner_group_id)
        return queryset.none()
