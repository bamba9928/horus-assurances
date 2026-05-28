from django.db import migrations


def mark_form_rule_seed_metadata(apps, schema_editor):
    FormRule = apps.get_model("reference_data", "FormRule")
    for form_rule in FormRule.objects.all():
        metadata = form_rule.metadata or {}
        metadata.update({"is_seed": True, "is_exhaustive": False})
        form_rule.metadata = metadata
        form_rule.save(update_fields=["metadata"])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("reference_data", "0005_formrule_metadata"),
    ]

    operations = [
        migrations.RunPython(mark_form_rule_seed_metadata, noop_reverse),
    ]
