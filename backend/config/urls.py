from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.accounts.views import UserViewSet
from apps.clients.views import ClientViewSet
from apps.contracts.views import ContractViewSet
from apps.groups.views import PartnerGroupViewSet
from apps.payments.views import GroupWalletViewSet, PaymentViewSet, WalletTransactionViewSet
from apps.quotes.views import QuoteViewSet
from apps.vehicles.views import VehicleViewSet

router = DefaultRouter()
router.register("groups", PartnerGroupViewSet, basename="partnergroup")
router.register("users", UserViewSet, basename="user")
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

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/v1/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/v1/", include(router.urls)),
]
