from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.accounts.views import AuthMeView, ContributorViewSet, UserViewSet
from apps.audit.views import AuditLogViewSet
from apps.clients.views import (
    ClientPortalAttestationDownloadView,
    ClientPortalCarteBruneDownloadView,
    ClientPortalContractDocumentsView,
    ClientPortalContractListView,
    ClientPortalDocumentOtpCreateView,
    ClientPortalNotificationListView,
    ClientPortalNotificationMarkAllReadView,
    ClientPortalNotificationMarkReadView,
    ClientPortalProfileView,
    ClientAccessTokenViewSet,
    ClientViewSet,
)
from apps.commissions.views import CommissionRuleViewSet, CommissionViewSet
from apps.contracts.views import ContractViewSet
from apps.common.views import DashboardView
from apps.groups.views import PartnerGroupViewSet
from apps.notifications.views import NotificationViewSet
from apps.payments.views import (
    GroupWalletViewSet,
    OrangeMoneyWebhookView,
    PaymentViewSet,
    WalletTransactionViewSet,
    WaveWebhookView,
)
from apps.quotes.views import QuoteViewSet
from apps.vehicles.views import VehicleViewSet

router = DefaultRouter()
router.register("groups", PartnerGroupViewSet, basename="partnergroup")
router.register("users", UserViewSet, basename="user")
router.register("contributors", ContributorViewSet, basename="contributor")
router.register("clients", ClientViewSet, basename="client")
router.register("client-access-tokens", ClientAccessTokenViewSet, basename="clientaccesstoken")
router.register("vehicles", VehicleViewSet, basename="vehicle")
router.register("quotes", QuoteViewSet, basename="quote")
router.register("wallets", GroupWalletViewSet, basename="wallet")
router.register(
    "wallet-transactions",
    WalletTransactionViewSet,
    basename="wallettransaction",
)
router.register("payments", PaymentViewSet, basename="payment")
router.register("contracts", ContractViewSet, basename="contract")
router.register("commission-rules", CommissionRuleViewSet, basename="commissionrule")
router.register("commissions", CommissionViewSet, basename="commission")
router.register("audit-logs", AuditLogViewSet, basename="auditlog")
router.register("notifications", NotificationViewSet, basename="notification")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("api/auth/login/", TokenObtainPairView.as_view(), name="auth_login"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="auth_token_refresh"),
    path("api/auth/me/", AuthMeView.as_view(), name="auth_me"),
    path("api/dashboard/", DashboardView.as_view(), name="dashboard"),
    path("api/v1/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/v1/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/v1/auth/me/", AuthMeView.as_view(), name="token_me"),
    path("api/v1/dashboard/", DashboardView.as_view(), name="dashboard_v1"),
    path("api/v1/webhooks/wave/", WaveWebhookView.as_view(), name="wave_webhook"),
    path(
        "api/v1/webhooks/orange-money/",
        OrangeMoneyWebhookView.as_view(),
        name="orange_money_webhook",
    ),
    path("api/v1/client-space/me/", ClientPortalProfileView.as_view(), name="client_space_me"),
    path(
        "api/v1/client-space/contracts/",
        ClientPortalContractListView.as_view(),
        name="client_space_contracts",
    ),
    path(
        "api/v1/client-space/contracts/<int:pk>/documents/",
        ClientPortalContractDocumentsView.as_view(),
        name="client_space_contract_documents",
    ),
    path(
        "api/v1/client-space/contracts/<int:pk>/documents/otp/",
        ClientPortalDocumentOtpCreateView.as_view(),
        name="client_space_contract_document_otp",
    ),
    path(
        "api/v1/client-space/contracts/<int:pk>/documents/attestation/",
        ClientPortalAttestationDownloadView.as_view(),
        name="client_space_contract_attestation",
    ),
    path(
        "api/v1/client-space/contracts/<int:pk>/documents/carte-brune/",
        ClientPortalCarteBruneDownloadView.as_view(),
        name="client_space_contract_carte_brune",
    ),
    path(
        "api/v1/client-space/notifications/",
        ClientPortalNotificationListView.as_view(),
        name="client_space_notifications",
    ),
    path(
        "api/v1/client-space/notifications/mark-all-read/",
        ClientPortalNotificationMarkAllReadView.as_view(),
        name="client_space_notifications_mark_all_read",
    ),
    path(
        "api/v1/client-space/notifications/<int:pk>/mark-read/",
        ClientPortalNotificationMarkReadView.as_view(),
        name="client_space_notification_mark_read",
    ),
    path("api/v1/", include(router.urls)),
    path("api/webhooks/wave/", WaveWebhookView.as_view(), name="wave_webhook_alias"),
    path(
        "api/webhooks/orange-money/",
        OrangeMoneyWebhookView.as_view(),
        name="orange_money_webhook_alias",
    ),
    path("api/client-space/me/", ClientPortalProfileView.as_view(), name="client_space_me_alias"),
    path(
        "api/client-space/contracts/",
        ClientPortalContractListView.as_view(),
        name="client_space_contracts_alias",
    ),
    path(
        "api/client-space/contracts/<int:pk>/documents/",
        ClientPortalContractDocumentsView.as_view(),
        name="client_space_contract_documents_alias",
    ),
    path(
        "api/client-space/contracts/<int:pk>/documents/otp/",
        ClientPortalDocumentOtpCreateView.as_view(),
        name="client_space_contract_document_otp_alias",
    ),
    path(
        "api/client-space/contracts/<int:pk>/documents/attestation/",
        ClientPortalAttestationDownloadView.as_view(),
        name="client_space_contract_attestation_alias",
    ),
    path(
        "api/client-space/contracts/<int:pk>/documents/carte-brune/",
        ClientPortalCarteBruneDownloadView.as_view(),
        name="client_space_contract_carte_brune_alias",
    ),
    path(
        "api/client-space/notifications/",
        ClientPortalNotificationListView.as_view(),
        name="client_space_notifications_alias",
    ),
    path(
        "api/client-space/notifications/mark-all-read/",
        ClientPortalNotificationMarkAllReadView.as_view(),
        name="client_space_notifications_mark_all_read_alias",
    ),
    path(
        "api/client-space/notifications/<int:pk>/mark-read/",
        ClientPortalNotificationMarkReadView.as_view(),
        name="client_space_notification_mark_read_alias",
    ),
    path("api/", include(router.urls)),
]
