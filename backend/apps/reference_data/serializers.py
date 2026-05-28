from rest_framework import serializers

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


class ProductReferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductReference
        fields = [
            "id",
            "code",
            "ass_code",
            "label",
            "description",
            "source",
            "is_active",
            "is_verified",
            "sort_order",
            "metadata",
        ]
        read_only_fields = fields


class VehicleBrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleBrand
        fields = [
            "id",
            "code",
            "ass_code",
            "label",
            "source",
            "is_active",
            "is_verified",
            "sort_order",
            "metadata",
        ]
        read_only_fields = fields


class VehicleCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleCategory
        fields = [
            "id",
            "code",
            "ass_code",
            "label",
            "source",
            "is_active",
            "is_verified",
            "sort_order",
            "metadata",
        ]
        read_only_fields = fields


class VehicleSubCategorySerializer(serializers.ModelSerializer):
    category_code = serializers.CharField(source="category.code", read_only=True)
    category_label = serializers.CharField(source="category.label", read_only=True)

    class Meta:
        model = VehicleSubCategory
        fields = [
            "id",
            "category",
            "category_code",
            "category_label",
            "code",
            "ass_code",
            "label",
            "source",
            "is_active",
            "is_verified",
            "sort_order",
            "metadata",
        ]
        read_only_fields = fields


class VehicleGenreSerializer(serializers.ModelSerializer):
    category_code = serializers.CharField(source="category.code", read_only=True)
    category_label = serializers.CharField(source="category.label", read_only=True)
    subcategory_code = serializers.CharField(source="subcategory.code", read_only=True)
    subcategory_label = serializers.CharField(source="subcategory.label", read_only=True)

    class Meta:
        model = VehicleGenre
        fields = [
            "id",
            "category",
            "category_code",
            "category_label",
            "subcategory",
            "subcategory_code",
            "subcategory_label",
            "code",
            "ass_code",
            "label",
            "requires_trailer_section",
            "source",
            "is_active",
            "is_verified",
            "sort_order",
            "metadata",
        ]
        read_only_fields = fields


class EnergyTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EnergyType
        fields = [
            "id",
            "code",
            "ass_code",
            "label",
            "source",
            "is_active",
            "is_verified",
            "sort_order",
            "metadata",
        ]
        read_only_fields = fields


class VehicleUsageSerializer(serializers.ModelSerializer):
    product_code = serializers.CharField(source="product.code", read_only=True)
    product_label = serializers.CharField(source="product.label", read_only=True)

    class Meta:
        model = VehicleUsage
        fields = [
            "id",
            "product",
            "product_code",
            "product_label",
            "code",
            "ass_code",
            "label",
            "source",
            "is_active",
            "is_verified",
            "sort_order",
            "metadata",
        ]
        read_only_fields = fields


class GuaranteeReferenceSerializer(serializers.ModelSerializer):
    product_codes = serializers.SerializerMethodField()

    class Meta:
        model = GuaranteeReference
        fields = [
            "id",
            "code",
            "ass_code",
            "ass_id",
            "label",
            "product_codes",
            "is_mandatory",
            "is_default_selected",
            "is_readonly",
            "source",
            "is_active",
            "is_verified",
            "sort_order",
            "metadata",
        ]
        read_only_fields = fields

    def get_product_codes(self, obj):
        return [product.code for product in obj.products.all()]


class DurationOptionSerializer(serializers.ModelSerializer):
    product_code = serializers.CharField(source="product.code", read_only=True)
    product_label = serializers.CharField(source="product.label", read_only=True)

    class Meta:
        model = DurationOption
        fields = [
            "id",
            "product",
            "product_code",
            "product_label",
            "code",
            "ass_code",
            "label",
            "duration",
            "periodicity",
            "ass_duration",
            "ass_periodicity",
            "source",
            "is_active",
            "is_verified",
            "sort_order",
            "metadata",
        ]
        read_only_fields = fields


class FormRuleSerializer(serializers.ModelSerializer):
    product_code = serializers.CharField(source="product.code", read_only=True)
    category_code = serializers.CharField(source="category.code", read_only=True)
    subcategory_code = serializers.CharField(source="subcategory.code", read_only=True)
    genre_code = serializers.CharField(source="genre.code", read_only=True)

    class Meta:
        model = FormRule
        fields = [
            "id",
            "code",
            "product",
            "product_code",
            "category",
            "category_code",
            "subcategory",
            "subcategory_code",
            "genre",
            "genre_code",
            "field_name",
            "rule_type",
            "value",
            "metadata",
            "source",
            "is_active",
            "is_verified",
            "priority",
        ]
        read_only_fields = fields
