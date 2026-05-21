from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Commission, CommissionRule
from .serializers import (
    CommissionGenerateSerializer,
    CommissionRuleSerializer,
    CommissionSerializer,
)
from .services import generate_commission_for_contract, mark_commission_paid


class CommissionRuleViewSet(viewsets.ModelViewSet):
    serializer_class = CommissionRuleSerializer
    filterset_fields = ["partner_group", "contributor", "is_active"]
    ordering_fields = ["id", "created_at", "updated_at", "percentage_rate", "fixed_amount"]
    ordering = ["id"]

    def get_queryset(self):
        user = self.request.user
        queryset = CommissionRule.objects.select_related("partner_group", "contributor")

        if user.is_general_admin:
            return queryset
        if user.is_group_admin:
            return queryset.filter(partner_group=user.partner_group)
        return queryset.none()


class CommissionViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = CommissionSerializer
    filterset_fields = ["partner_group", "contract", "payment", "contributor", "status"]
    ordering_fields = ["id", "created_at", "generated_at", "paid_at", "amount"]
    ordering = ["id"]

    def get_queryset(self):
        user = self.request.user
        queryset = Commission.objects.select_related(
            "partner_group",
            "contract",
            "payment",
            "contributor",
            "rule",
        )

        if user.is_general_admin:
            return queryset
        if user.is_group_admin:
            return queryset.filter(partner_group=user.partner_group)
        if user.is_contributor:
            return queryset.filter(contributor=user)
        return queryset.none()

    @action(detail=False, methods=["post"], url_path="generate-for-contract")
    def generate_for_contract(self, request):
        serializer = CommissionGenerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        contract = serializer.validated_data["contract"]

        if not self._can_use_contract(contract):
            return Response(
                {"detail": "Contrat introuvable."},
                status=status.HTTP_404_NOT_FOUND,
            )

        commission = generate_commission_for_contract(contract=contract)
        return Response(
            CommissionSerializer(commission, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="mark-paid")
    def mark_paid(self, request, pk=None):
        if request.user.is_contributor:
            return Response(
                {"detail": "Action non autorisee."},
                status=status.HTTP_403_FORBIDDEN,
            )
        commission = self.get_object()
        commission = mark_commission_paid(commission=commission)
        return Response(CommissionSerializer(commission, context={"request": request}).data)

    def _can_use_contract(self, contract):
        user = self.request.user
        if user.is_general_admin:
            return True
        if user.is_group_admin:
            return contract.partner_group_id == user.partner_group_id
        if user.is_contributor:
            return contract.contributor_id == user.id
        return False
