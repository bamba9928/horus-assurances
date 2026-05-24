from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from django.shortcuts import redirect
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.contracts.models import Contract
from apps.contracts.serializers import ContractDocumentsSerializer
from apps.notifications.models import Notification

from .models import Client, ClientAccessToken
from .portal import (
    authenticate_client_access_request,
    create_client_access_token,
    resend_client_access_link,
    revoke_client_access_token,
    rotate_client_access_token,
)
from .serializers import (
    ClientAccessTokenCreateSerializer,
    ClientAccessTokenRenewSerializer,
    ClientAccessTokenResponseSerializer,
    ClientAccessTokenSerializer,
    ClientPortalContractSerializer,
    ClientPortalNotificationSerializer,
    ClientPortalProfileSerializer,
    ClientSerializer,
)


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

class ClientAccessTokenViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = ClientAccessToken.objects.none()
    serializer_class = ClientAccessTokenSerializer
    filterset_fields = [
        "partner_group",
        "client",
        "contract",
        "delivery_channel",
        "revoked_at",
    ]
    ordering_fields = ["id", "created_at", "expires_at", "revoked_at", "used_at"]
    ordering = ["-created_at", "-id"]

    def get_queryset(self):
        user = self.request.user
        queryset = ClientAccessToken.objects.select_related(
            "partner_group",
            "client",
            "client__contributor",
            "contract",
            "created_by",
            "rotated_from",
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
            return queryset.filter(client__contributor=user)
        return queryset.none()

    def create(self, request, *args, **kwargs):
        serializer = ClientAccessTokenCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        client = serializer.validated_data["client"]
        contract = serializer.validated_data["contract"]
        if not self._can_use_client_contract(client=client, contract=contract):
            return Response({"detail": "Client ou contrat introuvable."}, status=status.HTTP_404_NOT_FOUND)

        raw_token, access_token, delivery = create_client_access_token(
            client=client,
            contract=contract,
            created_by=request.user,
            delivery_channel=serializer.validated_data["delivery_channel"],
            expires_in_days=serializer.validated_data.get("expires_in_days"),
        )
        return Response(
            _access_token_response(access_token, raw_token, delivery),
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="revoke")
    def revoke(self, request, pk=None):
        access_token = revoke_client_access_token(
            access_token=self.get_object(),
            actor=request.user,
        )
        return Response(ClientAccessTokenSerializer(access_token).data)

    @action(detail=True, methods=["post"], url_path="renew")
    def renew(self, request, pk=None):
        serializer = ClientAccessTokenRenewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        raw_token, access_token, delivery = rotate_client_access_token(
            access_token=self.get_object(),
            actor=request.user,
            expires_in_days=serializer.validated_data.get("expires_in_days"),
        )
        return Response(_access_token_response(access_token, raw_token, delivery))

    @action(detail=True, methods=["post"], url_path="resend-link")
    def resend_link(self, request, pk=None):
        raw_token, access_token, delivery = resend_client_access_link(
            access_token=self.get_object(),
            actor=request.user,
        )
        return Response(_access_token_response(access_token, raw_token, delivery))

    def _can_use_client_contract(self, *, client, contract):
        if contract.client_id != client.id:
            return False
        if contract.partner_group_id != client.partner_group_id:
            return False

        user = self.request.user
        if user.is_general_admin:
            return True
        if user.is_group_admin:
            return client.partner_group_id == user.partner_group_id
        if user.is_contributor:
            return client.contributor_id == user.id
        return False


class ClientPortalBaseView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get_access_token(self, request):
        return authenticate_client_access_request(request)


class ClientPortalProfileView(ClientPortalBaseView):
    @extend_schema(
        responses={200: ClientPortalProfileSerializer},
        auth=[],
    )
    def get(self, request):
        access_token = self.get_access_token(request)
        return Response(ClientPortalProfileSerializer(access_token.client).data)


class ClientPortalContractListView(ClientPortalBaseView):
    @extend_schema(
        responses={200: ClientPortalContractSerializer(many=True)},
        auth=[],
    )
    def get(self, request):
        access_token = self.get_access_token(request)
        contracts = _client_contracts(access_token)
        return Response(ClientPortalContractSerializer(contracts, many=True).data)


class ClientPortalContractDocumentsView(ClientPortalBaseView):
    @extend_schema(
        responses={200: ContractDocumentsSerializer},
        auth=[],
    )
    def get(self, request, pk):
        access_token = self.get_access_token(request)
        contract = _client_contracts(access_token).filter(pk=pk).first()
        if contract is None:
            return Response({"detail": "Contrat introuvable."}, status=status.HTTP_404_NOT_FOUND)
        return Response(ContractDocumentsSerializer(contract).data)


class ClientPortalContractDocumentDownloadView(ClientPortalBaseView):
    document_kind = ""

    @extend_schema(
        responses={302: OpenApiTypes.NONE, 404: OpenApiTypes.OBJECT},
        auth=[],
    )
    def get(self, request, pk):
        access_token = self.get_access_token(request)
        contract = _client_contracts(access_token).filter(pk=pk).first()
        if contract is None:
            return Response({"detail": "Contrat introuvable."}, status=status.HTTP_404_NOT_FOUND)

        document_url = getattr(contract, self.document_kind, "")
        if not document_url:
            return Response({"detail": "Document indisponible."}, status=status.HTTP_404_NOT_FOUND)
        return redirect(document_url)


class ClientPortalAttestationDownloadView(ClientPortalContractDocumentDownloadView):
    document_kind = "attestation_url"


class ClientPortalCarteBruneDownloadView(ClientPortalContractDocumentDownloadView):
    document_kind = "carte_brune_url"


class ClientPortalNotificationListView(ClientPortalBaseView):
    @extend_schema(
        responses={200: ClientPortalNotificationSerializer(many=True)},
        auth=[],
    )
    def get(self, request):
        access_token = self.get_access_token(request)
        notifications = _client_notifications(access_token.client)
        return Response(ClientPortalNotificationSerializer(notifications, many=True).data)


class ClientPortalNotificationMarkReadView(ClientPortalBaseView):
    @extend_schema(
        request=None,
        responses={200: ClientPortalNotificationSerializer},
        auth=[],
    )
    def post(self, request, pk):
        access_token = self.get_access_token(request)
        notification = _client_notifications(access_token.client).filter(pk=pk).first()
        if notification is None:
            return Response(
                {"detail": "Notification introuvable."},
                status=status.HTTP_404_NOT_FOUND,
            )
        if notification.read_at is None:
            notification.read_at = timezone.now()
            notification.save(update_fields=["read_at"])
        return Response(ClientPortalNotificationSerializer(notification).data)


class ClientPortalNotificationMarkAllReadView(ClientPortalBaseView):
    @extend_schema(
        request=None,
        responses={200: OpenApiTypes.OBJECT},
        auth=[],
    )
    def post(self, request):
        access_token = self.get_access_token(request)
        updated_count = _client_notifications(access_token.client).filter(read_at__isnull=True).update(
            read_at=timezone.now()
        )
        return Response({"marked_read": updated_count}, status=status.HTTP_200_OK)


def _client_contracts(access_token):
    return Contract.objects.select_related("quote", "vehicle").filter(
        pk=access_token.contract_id,
        client=access_token.client,
        partner_group=access_token.partner_group,
    ).order_by(
        "-created_at",
        "-id",
    )


def _client_notifications(client):
    return Notification.objects.filter(client=client).order_by("-created_at", "-id")


def _access_token_response(access_token, raw_token, delivery):
    payload = {
        "access_token": ClientAccessTokenSerializer(access_token).data,
        "token": raw_token,
        "access_url": delivery["access_url"],
        "mock_delivery": delivery["mock_delivery"],
        "delivery_channel": delivery["delivery_channel"],
        "destination": delivery["destination"],
        "expires_at": access_token.expires_at,
    }
    return ClientAccessTokenResponseSerializer(payload).data
