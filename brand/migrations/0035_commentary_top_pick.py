# Generated by Django 4.1.7 on 2023-09-22 12:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("brand", "0034_alter_commentary_details_alter_commentary_header_and_more")]

    operations = [
        migrations.AddField(
            model_name="commentary",
            name="top_pick",
            field=models.BooleanField(default=False, help_text="Marks this brand as a top pick"),
        )
    ]
