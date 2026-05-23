from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("quotes", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="quote",
            name="ass_product_data",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
