from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Quote
from .serializers import QuoteCalculateSerializer, QuoteSerializer


class QuoteViewSet(viewsets.ModelViewSet):
    queryset = Quote.objects.none()
    serializer_class = QuoteSerializer
    filterset_fields = [
        "partner_group",
        "client",
        "vehicle",
        "contributor",
        "status",
        "product_type",
    ]
    search_fields = [
        "client__first_name",
        "client__last_name",
        "client__company_name",
        "vehicle__registration_number",
    ]
    ordering_fields = ["id", "created_at", "updated_at", "effective_date"]
    ordering = ["id"]

    def get_queryset(self):
        user = self.request.user
        queryset = Quote.objects.select_related(
            "partner_group",
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
    def calculate(self, request, pk=None):
        quote = self.get_object()
        serializer = QuoteCalculateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        for field, value in serializer.validated_data.items():
            setattr(quote, field, value)

        quote.status = Quote.Status.CALCULATED
        quote.refresh_total_amount()
        quote.full_clean()
        quote.save()

        return Response(QuoteSerializer(quote, context={"request": request}).data, status=status.HTTP_200_OK)
