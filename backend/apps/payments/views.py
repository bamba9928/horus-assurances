from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.groups.models import PartnerGroup

from .models import GroupWallet, Payment, PaymentWebhookEvent, WalletTransaction
from .serializers import (
    GroupWalletSerializer,
    PaymentConfirmSerializer,
    PaymentSerializer,
    WalletActionSerializer,
    WalletTransactionSerializer,
)
from .services import confirm_payment, credit_wallet, debit_wallet, get_or_create_wallet
from .webhooks import (
    WebhookConfigurationError,
    WebhookProcessingError,
    WebhookSignatureError,
    process_orange_money_webhook,
    process_wave_webhook,
)


class PaymentWebhookView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    provider = None

    @extend_schema(
        request=OpenApiTypes.OBJECT,
        responses={200: OpenApiTypes.OBJECT},
        auth=[],
    )
    def post(self, request):
        try:
            result = self._process(request)
        except WebhookSignatureError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_401_UNAUTHORIZED)
        except WebhookConfigurationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except WebhookProcessingError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except serializers.ValidationError as exc:
            return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "status": "duplicate" if result.duplicate else result.event.status,
                "event_id": result.event.event_id,
            },
            status=status.HTTP_200_OK,
        )

    def _process(self, request):
        if self.provider == PaymentWebhookEvent.Provider.WAVE:
            return process_wave_webhook(
                raw_body=request.body,
                headers=request.headers,
            )
        if self.provider == PaymentWebhookEvent.Provider.ORANGE_MONEY:
            return process_orange_money_webhook(
                raw_body=request.body,
                headers=request.headers,
            )
        raise WebhookProcessingError("Provider webhook inconnu.")


class WaveWebhookView(PaymentWebhookView):
    provider = PaymentWebhookEvent.Provider.WAVE


class OrangeMoneyWebhookView(PaymentWebhookView):
    provider = PaymentWebhookEvent.Provider.ORANGE_MONEY


class GroupWalletViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = GroupWallet.objects.none()
    serializer_class = GroupWalletSerializer
    filterset_fields = ["partner_group", "currency"]
    ordering_fields = ["id", "balance", "created_at", "updated_at"]
    ordering = ["id"]

    def _ensure_accessible_wallets(self):
        user = self.request.user
        if getattr(self, "swagger_fake_view", False):
            return
        if not user or not user.is_authenticated:
            return
        if user.is_general_admin:
            for partner_group in PartnerGroup.objects.all():
                get_or_create_wallet(partner_group)
        elif user.is_group_admin:
            get_or_create_wallet(user.partner_group)

    def get_queryset(self):
        user = self.request.user
        self._ensure_accessible_wallets()
        queryset = GroupWallet.objects.select_related("partner_group")

        if getattr(self, "swagger_fake_view", False):
            return queryset.none()
        if not user or not user.is_authenticated:
            return queryset.none()
        if user.is_general_admin:
            return queryset
        if user.is_group_admin:
            return queryset.filter(partner_group=user.partner_group)
        return queryset.none()

    @action(detail=True, methods=["post"])
    def credit(self, request, pk=None):
        wallet = self.get_object()
        serializer = WalletActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        wallet_transaction = credit_wallet(
            wallet=wallet,
            amount=serializer.validated_data["amount"],
            created_by=request.user,
            idempotency_key=serializer.validated_data.get("idempotency_key", ""),
            reference=serializer.validated_data.get("reference", ""),
        )
        return Response(
            WalletTransactionSerializer(wallet_transaction).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def debit(self, request, pk=None):
        wallet = self.get_object()
        serializer = WalletActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        wallet_transaction = debit_wallet(
            wallet=wallet,
            amount=serializer.validated_data["amount"],
            created_by=request.user,
            idempotency_key=serializer.validated_data.get("idempotency_key", ""),
            reference=serializer.validated_data.get("reference", ""),
        )
        return Response(
            WalletTransactionSerializer(wallet_transaction).data,
            status=status.HTTP_200_OK,
        )


class WalletTransactionViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = WalletTransaction.objects.none()
    serializer_class = WalletTransactionSerializer
    filterset_fields = ["partner_group", "wallet", "transaction_type", "direction"]
    ordering_fields = ["id", "created_at", "amount"]
    ordering = ["id"]

    def get_queryset(self):
        user = self.request.user
        queryset = WalletTransaction.objects.select_related(
            "wallet",
            "partner_group",
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
        return queryset.none()


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.none()
    serializer_class = PaymentSerializer
    filterset_fields = ["partner_group", "quote", "client", "contributor", "method", "status"]
    search_fields = ["external_reference", "idempotency_key", "quote__reference"]
    ordering_fields = ["id", "created_at", "updated_at", "confirmed_at", "amount"]
    ordering = ["id"]

    def get_queryset(self):
        user = self.request.user
        queryset = Payment.objects.select_related(
            "partner_group",
            "quote",
            "client",
            "contributor",
            "created_by",
            "wallet_transaction",
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
    def confirm(self, request, pk=None):
        payment = self.get_object()
        serializer = PaymentConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment = confirm_payment(
            payment=payment,
            confirmed_by=request.user,
            idempotency_key=serializer.validated_data.get("idempotency_key", ""),
        )
        return Response(PaymentSerializer(payment, context={"request": request}).data)
