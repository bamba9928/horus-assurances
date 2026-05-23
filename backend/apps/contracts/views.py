from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Contract
from .serializers import (
    ContractDocumentsSerializer,
    ContractFromPaymentSerializer,
    ContractSerializer,
)
from .services import (
    build_contract_ass_payload_preview,
    create_contract_from_payment,
    issue_contract,
)


class ContractViewSet(viewsets.ModelViewSet):
    queryset = Contract.objects.none()
    serializer_class = ContractSerializer
    filterset_fields = [
        "partner_group",
        "quote",
        "payment",
        "client",
        "vehicle",
        "contributor",
        "status",
    ]
    search_fields = [
        "contract_number",
        "attestation_reference",
        "qr_code_reference",
        "client__first_name",
        "client__last_name",
        "client__company_name",
        "vehicle__registration_number",
    ]
    ordering_fields = ["id", "created_at", "updated_at", "issued_at"]
    ordering = ["id"]

    def get_queryset(self):
        user = self.request.user
        queryset = Contract.objects.select_related(
            "partner_group",
            "quote",
            "payment",
            "client",
            "vehicle",
            "contributor",
            "created_by",
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

    @action(detail=True, methods=["post"])
    def issue(self, request, pk=None):
        contract = self.get_object()
        contract = issue_contract(contract=contract, actor=request.user)
        return Response(ContractSerializer(contract, context={"request": request}).data)

    @action(detail=True, methods=["post"], url_path="ass-payload-preview")
    def ass_payload_preview(self, request, pk=None):
        contract = self.get_object()
        return Response(
            build_contract_ass_payload_preview(contract=contract),
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get"], url_path="documents")
    def documents(self, request, pk=None):
        contract = self.get_object()
        return Response(
            ContractDocumentsSerializer(contract, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["post"], url_path="create-from-payment")
    def create_from_payment(self, request):
        serializer = ContractFromPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment = serializer.validated_data["payment"]

        if not self._can_use_payment(payment):
            return Response(
                {"detail": "Paiement introuvable."},
                status=status.HTTP_404_NOT_FOUND,
            )

        contract = create_contract_from_payment(
            payment=payment,
            created_by=request.user,
        )
        return Response(
            ContractSerializer(contract, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    def _can_use_payment(self, payment):
        user = self.request.user
        if user.is_general_admin:
            return True
        if user.is_group_admin:
            return payment.partner_group_id == user.partner_group_id
        if user.is_contributor:
            return payment.contributor_id == user.id
        return False
