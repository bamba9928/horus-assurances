from django.core.exceptions import ValidationError
from django.db import models


class ActiveReferenceQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)


class ReferenceSource(models.TextChoices):
    DOCUMENTATION = "DOCUMENTATION", "Documentation ASS"
    POSTMAN = "POSTMAN", "Collection Postman"
    NATIVE_ACCOUNT = "NATIVE_ACCOUNT", "Compte natif ASS"
    SANDBOX_VALIDATION = "SANDBOX_VALIDATION", "Validation sandbox"
    INTERNAL = "INTERNAL", "Interne Horus"
    UNKNOWN = "UNKNOWN", "Inconnue"


class ReferenceBaseModel(models.Model):
    code = models.CharField(max_length=60, unique=True)
    ass_code = models.CharField(max_length=120, blank=True)
    label = models.CharField(max_length=180)
    source = models.CharField(
        max_length=30,
        choices=ReferenceSource.choices,
        default=ReferenceSource.INTERNAL,
    )
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    sort_order = models.PositiveSmallIntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ActiveReferenceQuerySet.as_manager()

    class Meta:
        abstract = True
        ordering = ["sort_order", "label", "id"]

    def __str__(self) -> str:
        return self.label


class ProductReference(ReferenceBaseModel):
    description = models.TextField(blank=True)


class VehicleBrand(ReferenceBaseModel):
    pass


class VehicleCategory(ReferenceBaseModel):
    pass


class VehicleSubCategory(ReferenceBaseModel):
    category = models.ForeignKey(
        VehicleCategory,
        on_delete=models.PROTECT,
        related_name="subcategories",
    )

    class Meta(ReferenceBaseModel.Meta):
        verbose_name_plural = "vehicle sub categories"


class VehicleGenre(ReferenceBaseModel):
    category = models.ForeignKey(
        VehicleCategory,
        on_delete=models.PROTECT,
        related_name="genres",
    )
    subcategory = models.ForeignKey(
        VehicleSubCategory,
        on_delete=models.PROTECT,
        related_name="genres",
        null=True,
        blank=True,
    )
    requires_trailer_section = models.BooleanField(default=False)

    def clean(self):
        super().clean()
        if (
            self.subcategory_id
            and self.category_id
            and self.subcategory.category_id != self.category_id
        ):
            raise ValidationError(
                {"subcategory": "La sous-categorie doit appartenir a la categorie."}
            )


class EnergyType(ReferenceBaseModel):
    pass


class VehicleUsage(ReferenceBaseModel):
    product = models.ForeignKey(
        ProductReference,
        on_delete=models.PROTECT,
        related_name="usages",
        null=True,
        blank=True,
    )


class GuaranteeReference(ReferenceBaseModel):
    ass_id = models.PositiveIntegerField(null=True, blank=True)
    products = models.ManyToManyField(
        ProductReference,
        related_name="guarantees",
        blank=True,
    )
    is_mandatory = models.BooleanField(default=False)
    is_default_selected = models.BooleanField(default=False)
    is_readonly = models.BooleanField(default=False)

    class Meta(ReferenceBaseModel.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["ass_id"],
                condition=models.Q(ass_id__isnull=False),
                name="reference_data_unique_guarantee_ass_id",
            )
        ]


class DurationOption(ReferenceBaseModel):
    class Periodicity(models.TextChoices):
        DAYS = "JOURS", "Jours"
        MONTHS = "MOIS", "Mois"
        YEARS = "ANNEES", "Annees"

    product = models.ForeignKey(
        ProductReference,
        on_delete=models.PROTECT,
        related_name="duration_options",
        null=True,
        blank=True,
    )
    duration = models.PositiveSmallIntegerField()
    periodicity = models.CharField(max_length=20, choices=Periodicity.choices)
    ass_duration = models.PositiveSmallIntegerField(null=True, blank=True)
    ass_periodicity = models.CharField(max_length=20, blank=True)


class FormRule(models.Model):
    class RuleType(models.TextChoices):
        SHOW = "SHOW", "Afficher"
        HIDE = "HIDE", "Masquer"
        REQUIRED = "REQUIRED", "Obligatoire"
        READONLY = "READONLY", "Lecture seule"
        DEFAULT = "DEFAULT", "Valeur par defaut"

    code = models.CharField(max_length=80, unique=True)
    product = models.ForeignKey(
        ProductReference,
        on_delete=models.PROTECT,
        related_name="form_rules",
        null=True,
        blank=True,
    )
    category = models.ForeignKey(
        VehicleCategory,
        on_delete=models.PROTECT,
        related_name="form_rules",
        null=True,
        blank=True,
    )
    subcategory = models.ForeignKey(
        VehicleSubCategory,
        on_delete=models.PROTECT,
        related_name="form_rules",
        null=True,
        blank=True,
    )
    genre = models.ForeignKey(
        VehicleGenre,
        on_delete=models.PROTECT,
        related_name="form_rules",
        null=True,
        blank=True,
    )
    field_name = models.CharField(max_length=120)
    rule_type = models.CharField(max_length=20, choices=RuleType.choices)
    value = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    source = models.CharField(
        max_length=30,
        choices=ReferenceSource.choices,
        default=ReferenceSource.INTERNAL,
    )
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    priority = models.PositiveSmallIntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ActiveReferenceQuerySet.as_manager()

    class Meta:
        ordering = ["priority", "code", "id"]

    def __str__(self) -> str:
        return self.code

    def clean(self):
        super().clean()
        if (
            self.subcategory_id
            and self.category_id
            and self.subcategory.category_id != self.category_id
        ):
            raise ValidationError(
                {"subcategory": "La sous-categorie doit appartenir a la categorie."}
            )
        if self.genre_id and self.category_id and self.genre.category_id != self.category_id:
            raise ValidationError(
                {"genre": "Le genre doit appartenir a la categorie."}
            )
        if (
            self.genre_id
            and self.subcategory_id
            and self.genre.subcategory_id
            and self.genre.subcategory_id != self.subcategory_id
        ):
            raise ValidationError(
                {"genre": "Le genre doit appartenir a la sous-categorie."}
            )
