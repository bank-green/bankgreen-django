# Generated by Django 4.1.7 on 2024-02-16 22:20

import brand.models.brand
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("brand", "0038_commentary_embrace")]

    operations = [
        migrations.AlterField(
            model_name="brand",
            name="tag",
            field=models.CharField(
                help_text="the tag we use or this brand record at Bank.Green. ",
                max_length=100,
                unique=True,
                validators=[brand.models.brand.validate_tag],
            ),
        ),
        migrations.DeleteModel(name="BrandUpdate"),
    ]
