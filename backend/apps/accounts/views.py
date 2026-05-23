from django.contrib.auth import get_user_model
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from rest_framework import viewsets

from .permissions import UserAccessPermission
from .serializers import ContributorSerializer, UserSerializer

User = get_user_model()


class AuthMeView(GenericAPIView):
    serializer_class = UserSerializer

    def get(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.none()
    serializer_class = UserSerializer
    permission_classes = [UserAccessPermission]
    filterset_fields = ["role", "partner_group", "is_active"]
    search_fields = ["username", "email", "first_name", "last_name", "phone"]
    ordering_fields = ["id", "username", "created_at"]
    ordering = ["id"]

    def get_queryset(self):
        user = self.request.user
        queryset = User.objects.select_related("partner_group").all()

        if getattr(self, "swagger_fake_view", False):
            return queryset.none()
        if not user or not user.is_authenticated:
            return queryset.none()
        if user.is_general_admin:
            return queryset
        if user.is_group_admin:
            return queryset.filter(partner_group=user.partner_group)
        if user.is_contributor:
            return queryset.filter(id=user.id)
        return queryset.none()


class ContributorViewSet(UserViewSet):
    serializer_class = ContributorSerializer

    def get_queryset(self):
        return super().get_queryset().filter(role=User.Role.CONTRIBUTOR)
