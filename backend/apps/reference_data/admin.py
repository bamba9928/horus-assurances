from django.contrib import admin

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


@admin.register(ProductReference)
class ProductReferenceAdmin(admin.ModelAdmin):
    list_display = ["code", "label", "ass_code", "source", "is_verified", "is_active", "sort_order"]
    list_filter = ["source", "is_verified", "is_active"]
    search_fields = ["code", "ass_code", "label"]


@admin.register(VehicleBrand)
class VehicleBrandAdmin(admin.ModelAdmin):
    list_display = ["code", "label", "ass_code", "source", "is_verified", "is_active", "sort_order"]
    list_filter = ["source", "is_verified", "is_active"]
    search_fields = ["code", "ass_code", "label"]


@admin.register(VehicleCategory)
class VehicleCategoryAdmin(admin.ModelAdmin):
    list_display = ["code", "label", "ass_code", "source", "is_verified", "is_active", "sort_order"]
    list_filter = ["source", "is_verified", "is_active"]
    search_fields = ["code", "ass_code", "label"]


@admin.register(VehicleSubCategory)
class VehicleSubCategoryAdmin(admin.ModelAdmin):
    list_display = [
        "code",
        "label",
        "category",
        "ass_code",
        "source",
        "is_verified",
        "is_active",
        "sort_order",
    ]
    list_filter = ["category", "source", "is_verified", "is_active"]
    search_fields = ["code", "ass_code", "label", "category__code"]


@admin.register(VehicleGenre)
class VehicleGenreAdmin(admin.ModelAdmin):
    list_display = [
        "code",
        "label",
        "category",
        "subcategory",
        "ass_code",
        "requires_trailer_section",
        "source",
        "is_verified",
        "is_active",
        "sort_order",
    ]
    list_filter = [
        "category",
        "subcategory",
        "requires_trailer_section",
        "source",
        "is_verified",
        "is_active",
    ]
    search_fields = ["code", "ass_code", "label", "category__code", "subcategory__code"]


@admin.register(EnergyType)
class EnergyTypeAdmin(admin.ModelAdmin):
    list_display = ["code", "label", "ass_code", "source", "is_verified", "is_active", "sort_order"]
    list_filter = ["source", "is_verified", "is_active"]
    search_fields = ["code", "ass_code", "label"]


@admin.register(VehicleUsage)
class VehicleUsageAdmin(admin.ModelAdmin):
    list_display = [
        "code",
        "label",
        "product",
        "ass_code",
        "source",
        "is_verified",
        "is_active",
        "sort_order",
    ]
    list_filter = ["product", "source", "is_verified", "is_active"]
    search_fields = ["code", "ass_code", "label", "product__code"]


@admin.register(GuaranteeReference)
class GuaranteeReferenceAdmin(admin.ModelAdmin):
    list_display = [
        "code",
        "label",
        "ass_code",
        "ass_id",
        "is_mandatory",
        "is_default_selected",
        "is_readonly",
        "source",
        "is_verified",
        "is_active",
        "sort_order",
    ]
    list_filter = [
        "is_mandatory",
        "is_default_selected",
        "is_readonly",
        "source",
        "is_verified",
        "is_active",
    ]
    search_fields = ["code", "ass_code", "label"]
    filter_horizontal = ["products"]


@admin.register(DurationOption)
class DurationOptionAdmin(admin.ModelAdmin):
    list_display = [
        "code",
        "label",
        "product",
        "duration",
        "periodicity",
        "source",
        "is_verified",
        "is_active",
        "sort_order",
    ]
    list_filter = ["product", "periodicity", "source", "is_verified", "is_active"]
    search_fields = ["code", "ass_code", "label", "product__code"]


@admin.register(FormRule)
class FormRuleAdmin(admin.ModelAdmin):
    list_display = [
        "code",
        "field_name",
        "rule_type",
        "product",
        "category",
        "subcategory",
        "genre",
        "source",
        "is_verified",
        "is_active",
        "priority",
    ]
    list_filter = [
        "rule_type",
        "product",
        "category",
        "subcategory",
        "genre",
        "source",
        "is_verified",
        "is_active",
    ]
    search_fields = ["code", "field_name", "product__code", "genre__code"]
