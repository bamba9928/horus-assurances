from django.db import migrations


REFERENCE_SOURCES = {
    "ProductReference": {
        "AUTO": ("SANDBOX_VALIDATION", True),
        "MOTO": ("SANDBOX_VALIDATION", True),
        "TRAILER": ("SANDBOX_VALIDATION", True),
        "SCHOOL_BUS": ("POSTMAN", False),
        "FLEET": ("POSTMAN", False),
        "GARAGE": ("POSTMAN", False),
    },
    "VehicleBrand": {
        "TOYOTA": ("INTERNAL", False),
        "HYUNDAI": ("INTERNAL", False),
        "KIA": ("INTERNAL", False),
        "RENAULT": ("INTERNAL", False),
        "PEUGEOT": ("INTERNAL", False),
        "MERCEDES_BENZ": ("INTERNAL", False),
        "NISSAN": ("INTERNAL", False),
        "FORD": ("INTERNAL", False),
        "HONDA": ("INTERNAL", False),
        "BMW": ("INTERNAL", False),
        "YAMAHA": ("INTERNAL", False),
        "SUZUKI": ("INTERNAL", False),
    },
    "VehicleCategory": {
        "TOURISME": ("NATIVE_ACCOUNT", False),
        "TRANSPORT_COMMERCIAL": ("NATIVE_ACCOUNT", False),
        "DEUX_ROUES": ("POSTMAN", False),
        "REMORQUE": ("POSTMAN", False),
    },
    "VehicleSubCategory": {
        "VEHICULE_PARTICULIER": ("NATIVE_ACCOUNT", False),
        "TPC_MOINS_3T500": ("NATIVE_ACCOUNT", False),
        "TPC_PLUS_3T500": ("NATIVE_ACCOUNT", False),
        "MOTO": ("POSTMAN", False),
        "REMORQUE": ("POSTMAN", False),
    },
    "VehicleGenre": {
        "VP": ("SANDBOX_VALIDATION", True),
        "TPC_MOINS_3T500": ("NATIVE_ACCOUNT", False),
        "TPC_PLUS_3T500": ("NATIVE_ACCOUNT", False),
        "BE_VTA": ("POSTMAN", False),
        "BE_VTCATP": ("POSTMAN", False),
        "MOTO": ("POSTMAN", False),
        "REMORQUE": ("SANDBOX_VALIDATION", True),
    },
    "EnergyType": {
        "ESSENCE": ("SANDBOX_VALIDATION", True),
        "DIESEL": ("POSTMAN", False),
        "ELECTRIQUE": ("POSTMAN", False),
        "HYBRIDE": ("POSTMAN", False),
    },
    "VehicleUsage": {
        "PRIVATE": ("INTERNAL", False),
        "PROFESSIONAL": ("INTERNAL", False),
        "NON_COMMERCIAL": ("POSTMAN", False),
        "COMMERCIAL": ("POSTMAN", False),
    },
    "GuaranteeReference": {
        "RC": ("NATIVE_ACCOUNT", False),
        "CEDEAO": ("NATIVE_ACCOUNT", False),
        "PERSONNES_TRANSPORTEES": ("NATIVE_ACCOUNT", False),
        "INCENDIE": ("NATIVE_ACCOUNT", False),
        "AVANCE_SUR_RECOURS": ("NATIVE_ACCOUNT", False),
        "DEFENSE_RECOURS": ("NATIVE_ACCOUNT", False),
        "VOL": ("NATIVE_ACCOUNT", False),
        "ASSISTANCE": ("NATIVE_ACCOUNT", False),
        "TIERCE_DOMMAGE": ("NATIVE_ACCOUNT", False),
        "COLLISION": ("NATIVE_ACCOUNT", False),
    },
    "DurationOption": {
        "1_MONTH": ("POSTMAN", False),
        "3_MONTHS": ("POSTMAN", False),
        "6_MONTHS": ("POSTMAN", False),
        "12_MONTHS": ("POSTMAN", False),
    },
    "FormRule": {
        "SHOW_TRAILER_SECTION_FOR_TPC_MOINS_3T500": ("NATIVE_ACCOUNT", False),
        "SHOW_TRAILER_SECTION_FOR_TPC_PLUS_3T500": ("NATIVE_ACCOUNT", False),
    },
}


def mark_reference_sources(apps, schema_editor):
    for model_name, values in REFERENCE_SOURCES.items():
        model = apps.get_model("reference_data", model_name)
        for code, (source, is_verified) in values.items():
            queryset = model.objects.filter(code=code)
            for reference in queryset:
                if hasattr(reference, "metadata"):
                    metadata = reference.metadata or {}
                    metadata.update({"is_seed": True, "is_exhaustive": False})
                    reference.metadata = metadata
                reference.source = source
                reference.is_verified = is_verified
                update_fields = ["source", "is_verified"]
                if hasattr(reference, "metadata"):
                    update_fields.append("metadata")
                reference.save(update_fields=update_fields)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("reference_data", "0003_durationoption_is_verified_durationoption_source_and_more"),
    ]

    operations = [
        migrations.RunPython(mark_reference_sources, noop_reverse),
    ]
