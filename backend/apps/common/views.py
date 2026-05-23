from django.contrib.auth import get_user_model
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.audit.models import AuditLog
from apps.clients.models import Client
from apps.commissions.models import Commission
from apps.contracts.models import Contract
from apps.groups.models import PartnerGroup
from apps.notifications.models import Notification
from apps.payments.models import GroupWallet, Payment
from apps.quotes.models import Quote
from apps.vehicles.models import Vehicle

from .serializers import DashboardSerializer

User = get_user_model()


class DashboardView(GenericAPIView):
    serializer_class = DashboardSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        data = {
            "scope": _scope_name(user),
            "counts": _dashboard_counts(user),
        }
        serializer = self.get_serializer(data)
        return Response(serializer.data)


def _scope_name(user):
    if user.is_general_admin:
        return "platform"
    if user.is_group_admin:
        return "group"
    if user.is_contributor:
        return "contributor"
    return "none"


def _dashboard_counts(user):
    if user.is_general_admin:
        return {
            "groups": PartnerGroup.objects.count(),
            "users": User.objects.count(),
            "contributors": User.objects.filter(role=User.Role.CONTRIBUTOR).count(),
            "clients": Client.objects.count(),
            "vehicles": Vehicle.objects.count(),
            "quotes": Quote.objects.count(),
            "payments": Payment.objects.count(),
            "confirmed_payments": Payment.objects.filter(
                status=Payment.Status.CONFIRMED
            ).count(),
            "contracts": Contract.objects.count(),
            "issued_contracts": Contract.objects.filter(
                status=Contract.Status.ISSUED
            ).count(),
            "commissions": Commission.objects.count(),
            "wallets": GroupWallet.objects.count(),
            "audit_logs": AuditLog.objects.count(),
            "unread_notifications": Notification.objects.filter(
                recipient=user,
                read_at__isnull=True,
            ).count(),
        }

    if user.is_group_admin:
        partner_group = user.partner_group
        return {
            "groups": PartnerGroup.objects.filter(id=user.partner_group_id).count(),
            "users": User.objects.filter(partner_group=partner_group).count(),
            "contributors": User.objects.filter(
                partner_group=partner_group,
                role=User.Role.CONTRIBUTOR,
            ).count(),
            "clients": Client.objects.filter(partner_group=partner_group).count(),
            "vehicles": Vehicle.objects.filter(partner_group=partner_group).count(),
            "quotes": Quote.objects.filter(partner_group=partner_group).count(),
            "payments": Payment.objects.filter(partner_group=partner_group).count(),
            "confirmed_payments": Payment.objects.filter(
                partner_group=partner_group,
                status=Payment.Status.CONFIRMED,
            ).count(),
            "contracts": Contract.objects.filter(partner_group=partner_group).count(),
            "issued_contracts": Contract.objects.filter(
                partner_group=partner_group,
                status=Contract.Status.ISSUED,
            ).count(),
            "commissions": Commission.objects.filter(partner_group=partner_group).count(),
            "wallets": GroupWallet.objects.filter(partner_group=partner_group).count(),
            "audit_logs": AuditLog.objects.filter(partner_group=partner_group).count(),
            "unread_notifications": Notification.objects.filter(
                recipient=user,
                read_at__isnull=True,
            ).count(),
        }

    if user.is_contributor:
        return {
            "groups": PartnerGroup.objects.filter(id=user.partner_group_id).count(),
            "users": 1,
            "contributors": 1,
            "clients": Client.objects.filter(contributor=user).count(),
            "vehicles": Vehicle.objects.filter(contributor=user).count(),
            "quotes": Quote.objects.filter(contributor=user).count(),
            "payments": Payment.objects.filter(contributor=user).count(),
            "confirmed_payments": Payment.objects.filter(
                contributor=user,
                status=Payment.Status.CONFIRMED,
            ).count(),
            "contracts": Contract.objects.filter(contributor=user).count(),
            "issued_contracts": Contract.objects.filter(
                contributor=user,
                status=Contract.Status.ISSUED,
            ).count(),
            "commissions": Commission.objects.filter(contributor=user).count(),
            "wallets": 0,
            "audit_logs": 0,
            "unread_notifications": Notification.objects.filter(
                recipient=user,
                read_at__isnull=True,
            ).count(),
        }

    return {}
