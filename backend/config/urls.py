from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.accounts.views import AuthMeView, ContributorViewSet, UserViewSet
from apps.audit.views import AuditLogViewSet
from apps.clients.views import ClientViewSet
from apps.commissions.views import CommissionRuleViewSet, CommissionViewSet
from apps.contracts.views import ContractViewSet
from apps.common.views import DashboardView
from apps.groups.views import PartnerGroupViewSet
from apps.notifications.views import NotificationViewSet
from apps.payments.views import GroupWalletViewSet, PaymentViewSet, WalletTransactionViewSet
from apps.quotes.views import QuoteViewSet
from apps.vehicles.views import VehicleViewSet

router = DefaultRouter()
router.register("groups", PartnerGroupViewSet, basename="partnergroup")
router.register("users", UserViewSet, basename="user")
router.register("contributors", ContributorViewSet, basename="contributor")
router.register("clients", ClientViewSet, basename="client")
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
    path("api/v1/", include(router.urls)),
    path("api/", include(router.urls)),
]
