from django.db.models import Q
from rest_framework import viewsets

from .models import (
    DurationOption,
    EnergyType,
    FormRule,
    GuaranteeReference,
    ProductReference,
    VehicleBrand,
    VehicleCategory,
    VehicleGenre,
    VehicleSubCategory,
    VehicleUsage,
)
from .serializers import (
    DurationOptionSerializer,
    EnergyTypeSerializer,
    FormRuleSerializer,
    GuaranteeReferenceSerializer,
    ProductReferenceSerializer,
    VehicleBrandSerializer,
    VehicleCategorySerializer,
    VehicleGenreSerializer,
    VehicleSubCategorySerializer,
    VehicleUsageSerializer,
)


class ActiveReferenceDataViewSet(viewsets.ReadOnlyModelViewSet):
    ordering_fields = ["id", "code", "label", "sort_order"]
    ordering = ["sort_order", "label", "id"]

    def get_queryset(self):
        queryset = super().get_queryset()
        if getattr(self, "swagger_fake_view", False):
            return queryset.none()
        if not self.request.user or not self.request.user.is_authenticated:
            return queryset.none()
        return self._filter_active_by_default(queryset)

    def _filter_active_by_default(self, queryset):
        include_inactive = self.request.query_params.get("include_inactive", "").lower()
        if "is_active" in self.request.query_params or include_inactive in ("1", "true"):
            return queryset
        return queryset.filter(is_active=True)


class ProductReferenceViewSet(ActiveReferenceDataViewSet):
    queryset = ProductReference.objects.all()
    serializer_class = ProductReferenceSerializer
    filterset_fields = ["code", "ass_code", "source", "is_verified", "is_active"]
    search_fields = ["code", "ass_code", "label", "description"]


class VehicleBrandViewSet(ActiveReferenceDataViewSet):
    queryset = VehicleBrand.objects.all()
    serializer_class = VehicleBrandSerializer
    filterset_fields = ["code", "ass_code", "source", "is_verified", "is_active"]
    search_fields = ["code", "ass_code", "label"]


class VehicleCategoryViewSet(ActiveReferenceDataViewSet):
    queryset = VehicleCategory.objects.all()
    serializer_class = VehicleCategorySerializer
    filterset_fields = ["code", "ass_code", "source", "is_verified", "is_active"]
    search_fields = ["code", "ass_code", "label"]


class VehicleSubCategoryViewSet(ActiveReferenceDataViewSet):
    queryset = VehicleSubCategory.objects.select_related("category")
    serializer_class = VehicleSubCategorySerializer
    filterset_fields = ["category", "code", "ass_code", "source", "is_verified", "is_active"]
    search_fields = ["code", "ass_code", "label", "category__code", "category__label"]

    def get_queryset(self):
        queryset = super().get_queryset()
        category_code = self.request.query_params.get("category_code")
        if category_code:
            queryset = queryset.filter(category__code=category_code)
        return queryset


class VehicleGenreViewSet(ActiveReferenceDataViewSet):
    queryset = VehicleGenre.objects.select_related("category", "subcategory")
    serializer_class = VehicleGenreSerializer
    filterset_fields = [
        "category",
        "subcategory",
        "code",
        "ass_code",
        "requires_trailer_section",
        "source",
        "is_verified",
        "is_active",
    ]
    search_fields = [
        "code",
        "ass_code",
        "label",
        "category__code",
        "subcategory__code",
    ]

    def get_queryset(self):
        queryset = super().get_queryset()
        category_code = self.request.query_params.get("category_code")
        subcategory_code = self.request.query_params.get("subcategory_code")
        if category_code:
            queryset = queryset.filter(category__code=category_code)
        if subcategory_code:
            queryset = queryset.filter(subcategory__code=subcategory_code)
        return queryset


class EnergyTypeViewSet(ActiveReferenceDataViewSet):
    queryset = EnergyType.objects.all()
    serializer_class = EnergyTypeSerializer
    filterset_fields = ["code", "ass_code", "source", "is_verified", "is_active"]
    search_fields = ["code", "ass_code", "label"]


class VehicleUsageViewSet(ActiveReferenceDataViewSet):
    queryset = VehicleUsage.objects.select_related("product")
    serializer_class = VehicleUsageSerializer
    filterset_fields = ["code", "ass_code", "source", "is_verified", "is_active"]
    search_fields = ["code", "ass_code", "label", "product__code"]

    def get_queryset(self):
        queryset = super().get_queryset()
        product = self.request.query_params.get("product_code") or self.request.query_params.get(
            "product"
        )
        if product:
            product_filter = Q(product__code=product) | Q(product__isnull=True)
            if str(product).isdigit():
                product_filter |= Q(product_id=int(product))
            queryset = queryset.filter(product_filter)
        return queryset


class GuaranteeReferenceViewSet(ActiveReferenceDataViewSet):
    queryset = GuaranteeReference.objects.prefetch_related("products")
    serializer_class = GuaranteeReferenceSerializer
    filterset_fields = [
        "code",
        "ass_code",
        "ass_id",
        "is_mandatory",
        "is_default_selected",
        "is_readonly",
        "source",
        "is_verified",
        "is_active",
    ]
    search_fields = ["code", "ass_code", "label"]

    def get_queryset(self):
        queryset = super().get_queryset()
        product = self.request.query_params.get("product_code") or self.request.query_params.get(
            "product"
        )
        if product:
            product_filter = Q(products__code=product) | Q(products__isnull=True)
            if str(product).isdigit():
                product_filter |= Q(products__id=int(product))
            queryset = queryset.filter(product_filter).distinct()
        return queryset


class DurationOptionViewSet(ActiveReferenceDataViewSet):
    queryset = DurationOption.objects.select_related("product")
    serializer_class = DurationOptionSerializer
    filterset_fields = [
        "duration",
        "periodicity",
        "code",
        "source",
        "is_verified",
        "is_active",
    ]
    search_fields = ["code", "ass_code", "label", "product__code"]

    def get_queryset(self):
        queryset = super().get_queryset()
        product = self.request.query_params.get("product_code") or self.request.query_params.get(
            "product"
        )
        if product:
            product_filter = Q(product__code=product) | Q(product__isnull=True)
            if str(product).isdigit():
                product_filter |= Q(product_id=int(product))
            queryset = queryset.filter(product_filter)
        return queryset


class FormRuleViewSet(ActiveReferenceDataViewSet):
    queryset = FormRule.objects.select_related(
        "product",
        "category",
        "subcategory",
        "genre",
    )
    serializer_class = FormRuleSerializer
    filterset_fields = [
        "product",
        "category",
        "subcategory",
        "genre",
        "field_name",
        "rule_type",
        "source",
        "is_verified",
        "is_active",
    ]
    search_fields = ["code", "field_name", "product__code", "genre__code"]
    ordering_fields = ["id", "code", "priority"]
    ordering = ["priority", "code", "id"]

    def get_queryset(self):
        queryset = super().get_queryset()
        for relation_name in ("product", "category", "subcategory", "genre"):
            value = self.request.query_params.get(f"{relation_name}_code")
            if value:
                queryset = queryset.filter(
                    Q(**{f"{relation_name}__code": value})
                    | Q(**{f"{relation_name}__isnull": True})
                )
        return queryset
