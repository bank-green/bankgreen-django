# Generated by Django 4.0.7 on 2022-12-13 13:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('datasource', '0002_remove_usnic_rssd_hd_usnic_control_usnic_country_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usnic',
            name='aba_prim',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AlterField(
            model_name='usnic',
            name='cusip',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AlterField(
            model_name='usnic',
            name='ein',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AlterField(
            model_name='usnic',
            name='fdic_cert',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AlterField(
            model_name='usnic',
            name='lei',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AlterField(
            model_name='usnic',
            name='ncua',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AlterField(
            model_name='usnic',
            name='occ',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AlterField(
            model_name='usnic',
            name='rssd',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AlterField(
            model_name='usnic',
            name='thrift',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AlterField(
            model_name='usnic',
            name='thrift_hc',
            field=models.CharField(blank=True, max_length=30),
        ),
    ]
