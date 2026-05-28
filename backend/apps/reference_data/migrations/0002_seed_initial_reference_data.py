from django.db import migrations


PRODUCTS = [
    ("AUTO", "AUTO", "Automobile", "Produit automobile individuel"),
    ("MOTO", "MOTO", "Moto", "Produit deux roues"),
    ("FLEET", "FLEET", "Flotte", "Proposition et contrat flotte"),
    ("TRAILER", "TRAILER", "Remorque", "Produit remorque"),
    ("SCHOOL_BUS", "SCHOOL_BUS", "Bus ecole", "Produit bus ecole"),
    ("GARAGE", "GARAGE", "Garage", "Produit garage"),
]

BRANDS = [
    ("TOYOTA", "TOYOTA", "Toyota"),
    ("HYUNDAI", "HYUNDAI", "Hyundai"),
    ("KIA", "KIA", "Kia"),
    ("RENAULT", "RENAULT", "Renault"),
    ("PEUGEOT", "PEUGEOT", "Peugeot"),
    ("MERCEDES_BENZ", "MERCEDES-BENZ", "Mercedes-Benz"),
    ("NISSAN", "NISSAN", "Nissan"),
    ("FORD", "FORD", "Ford"),
    ("HONDA", "HONDA", "Honda"),
    ("BMW", "BMW", "BMW"),
    ("YAMAHA", "YAMAHA", "Yamaha"),
    ("SUZUKI", "SUZUKI", "Suzuki"),
]

ENERGIES = [
    ("ESSENCE", "ESSENCE", "Essence"),
    ("DIESEL", "DIESEL", "Diesel"),
    ("ELECTRIQUE", "ELECTRIQUE", "Electrique"),
    ("HYBRIDE", "HYBRIDE", "Hybride"),
]

CATEGORIES = [
    ("TOURISME", "TOURISME", "Vehicules particuliers"),
    ("TRANSPORT_COMMERCIAL", "TRANSPORT_COMMERCIAL", "Transport commercial"),
    ("DEUX_ROUES", "DEUX_ROUES", "Deux roues"),
    ("REMORQUE", "REMORQUE", "Remorque"),
]

SUBCATEGORIES = [
    ("VEHICULE_PARTICULIER", "TOURISME", "VEHICULE_PARTICULIER", "Vehicule particulier"),
    ("TPC_MOINS_3T500", "TRANSPORT_COMMERCIAL", "TPC moins de 3t500", "TPC moins de 3t500"),
    ("TPC_PLUS_3T500", "TRANSPORT_COMMERCIAL", "TPC plus de 3t500", "TPC plus de 3t500"),
    ("MOTO", "DEUX_ROUES", "MOTO", "Moto"),
    ("REMORQUE", "REMORQUE", "REMORQUE", "Remorque"),
]

GENRES = [
    ("VP", "TOURISME", "VEHICULE_PARTICULIER", "VP", "Vehicule particulier", False, {}),
    (
        "TPC_MOINS_3T500",
        "TRANSPORT_COMMERCIAL",
        "TPC_MOINS_3T500",
        "TPC moins de 3t500",
        "TPC moins de 3t500",
        True,
        {"weight_band": "LT_3T500"},
    ),
    (
        "TPC_PLUS_3T500",
        "TRANSPORT_COMMERCIAL",
        "TPC_PLUS_3T500",
        "TPC plus de 3t500",
        "TPC plus de 3t500",
        True,
        {"weight_band": "GT_3T500"},
    ),
    ("BE_VTA", "TRANSPORT_COMMERCIAL", None, "BE-VTA", "Bus ecole VTA", False, {}),
    ("BE_VTCATP", "TRANSPORT_COMMERCIAL", None, "BE-VTCATP", "Bus ecole VTCATP", False, {}),
    ("MOTO", "DEUX_ROUES", "MOTO", "MOTO", "Moto", False, {}),
    ("REMORQUE", "REMORQUE", "REMORQUE", "REMORQUE", "Remorque", False, {}),
]

GUARANTEES = [
    ("RC", "RC", "Responsabilite civile", True, True, True),
    ("CEDEAO", "CEDEAO", "CEDEAO", True, True, True),
    ("PERSONNES_TRANSPORTEES", "PT", "Personnes transportees", False, False, False),
    ("INCENDIE", "INCENDIE", "Incendie", False, False, False),
    ("AVANCE_SUR_RECOURS", "AR", "Avance sur recours", False, False, False),
    ("DEFENSE_RECOURS", "DR", "Defense et recours", False, False, False),
    ("VOL", "VOL", "Vol", False, False, False),
    ("ASSISTANCE", "ASSISTANCE", "Assistance", False, False, False),
    ("TIERCE_DOMMAGE", "TIERCE_DOMMAGE", "Tierce dommage", False, False, False),
    ("COLLISION", "COLLISION", "Collision", False, False, False),
]

DURATIONS = [
    ("1_MONTH", "1 mois", 1, "MOIS"),
    ("3_MONTHS", "3 mois", 3, "MOIS"),
    ("6_MONTHS", "6 mois", 6, "MOIS"),
    ("12_MONTHS", "12 mois", 12, "MOIS"),
]

USAGES = [
    ("PRIVATE", "PRIVATE", "Prive", None),
    ("PROFESSIONAL", "PROFESSIONAL", "Professionnel", None),
    ("NON_COMMERCIAL", "NON_COMMERCIAL", "Non commercial", "MOTO"),
    ("COMMERCIAL", "COMMERCIAL", "Commercial", "MOTO"),
]


def seed_reference_data(apps, schema_editor):
    ProductReference = apps.get_model("reference_data", "ProductReference")
    VehicleBrand = apps.get_model("reference_data", "VehicleBrand")
    VehicleCategory = apps.get_model("reference_data", "VehicleCategory")
    VehicleSubCategory = apps.get_model("reference_data", "VehicleSubCategory")
    VehicleGenre = apps.get_model("reference_data", "VehicleGenre")
    EnergyType = apps.get_model("reference_data", "EnergyType")
    VehicleUsage = apps.get_model("reference_data", "VehicleUsage")
    GuaranteeReference = apps.get_model("reference_data", "GuaranteeReference")
    DurationOption = apps.get_model("reference_data", "DurationOption")
    FormRule = apps.get_model("reference_data", "FormRule")

    products = {}
    for sort_order, (code, ass_code, label, description) in enumerate(PRODUCTS, start=10):
        product, _ = ProductReference.objects.update_or_create(
            code=code,
            defaults={
                "ass_code": ass_code,
                "label": label,
                "description": description,
                "is_active": True,
                "sort_order": sort_order,
            },
        )
        products[code] = product

    for sort_order, (code, ass_code, label) in enumerate(BRANDS, start=10):
        VehicleBrand.objects.update_or_create(
            code=code,
            defaults={
                "ass_code": ass_code,
                "label": label,
                "is_active": True,
                "sort_order": sort_order,
            },
        )

    categories = {}
    for sort_order, (code, ass_code, label) in enumerate(CATEGORIES, start=10):
        category, _ = VehicleCategory.objects.update_or_create(
            code=code,
            defaults={
                "ass_code": ass_code,
                "label": label,
                "is_active": True,
                "sort_order": sort_order,
            },
        )
        categories[code] = category

    subcategories = {}
    for sort_order, (code, category_code, ass_code, label) in enumerate(
        SUBCATEGORIES,
        start=10,
    ):
        subcategory, _ = VehicleSubCategory.objects.update_or_create(
            code=code,
            defaults={
                "category": categories[category_code],
                "ass_code": ass_code,
                "label": label,
                "is_active": True,
                "sort_order": sort_order,
            },
        )
        subcategories[code] = subcategory

    genres = {}
    for sort_order, (
        code,
        category_code,
        subcategory_code,
        ass_code,
        label,
        requires_trailer_section,
        metadata,
    ) in enumerate(GENRES, start=10):
        genre, _ = VehicleGenre.objects.update_or_create(
            code=code,
            defaults={
                "category": categories[category_code],
                "subcategory": subcategories.get(subcategory_code),
                "ass_code": ass_code,
                "label": label,
                "requires_trailer_section": requires_trailer_section,
                "is_active": True,
                "sort_order": sort_order,
                "metadata": metadata,
            },
        )
        genres[code] = genre

    for sort_order, (code, ass_code, label) in enumerate(ENERGIES, start=10):
        EnergyType.objects.update_or_create(
            code=code,
            defaults={
                "ass_code": ass_code,
                "label": label,
                "is_active": True,
                "sort_order": sort_order,
            },
        )

    for sort_order, (code, ass_code, label, product_code) in enumerate(USAGES, start=10):
        VehicleUsage.objects.update_or_create(
            code=code,
            defaults={
                "product": products.get(product_code),
                "ass_code": ass_code,
                "label": label,
                "is_active": True,
                "sort_order": sort_order,
            },
        )

    for sort_order, (code, label, duration, periodicity) in enumerate(DURATIONS, start=10):
        DurationOption.objects.update_or_create(
            code=code,
            defaults={
                "ass_code": code,
                "label": label,
                "duration": duration,
                "periodicity": periodicity,
                "ass_duration": duration,
                "ass_periodicity": periodicity,
                "is_active": True,
                "sort_order": sort_order,
            },
        )

    for sort_order, (
        code,
        ass_code,
        label,
        is_mandatory,
        is_default_selected,
        is_readonly,
    ) in enumerate(GUARANTEES, start=10):
        GuaranteeReference.objects.update_or_create(
            code=code,
            defaults={
                "ass_code": ass_code,
                "label": label,
                "is_mandatory": is_mandatory,
                "is_default_selected": is_default_selected,
                "is_readonly": is_readonly,
                "is_active": True,
                "sort_order": sort_order,
            },
        )

    for genre_code in ("TPC_MOINS_3T500", "TPC_PLUS_3T500"):
        FormRule.objects.update_or_create(
            code=f"SHOW_TRAILER_SECTION_FOR_{genre_code}",
            defaults={
                "genre": genres[genre_code],
                "category": genres[genre_code].category,
                "subcategory": genres[genre_code].subcategory,
                "field_name": "trailer_section",
                "rule_type": "SHOW",
                "value": {
                    "fields": ["registration_number", "brand", "model"],
                    "source": "vehicle_genre.requires_trailer_section",
                },
                "is_active": True,
                "priority": 10,
            },
        )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("reference_data", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_reference_data, noop_reverse),
    ]
