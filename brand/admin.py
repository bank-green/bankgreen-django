from django.contrib import admin
from django.forms import ModelForm
from django.utils.html import format_html

from datasource.models.datasource import Datasource

from .models import Brand, Commentary


class CommentaryInline(admin.TabularInline):
    model = Commentary
    extra = 0
    # raw_id_fields = ["subsidiary_of_1", "subsidiary_of_2", "subsidiary_of_3", "subsidiary_of_4"]
    # fk_name = "brand"


class DatasourceInline(admin.TabularInline):
    model = Datasource
    extra = 0
    raw_id_fields = ["subsidiary_of_1", "subsidiary_of_2", "subsidiary_of_3", "subsidiary_of_4"]
    fk_name = "brand"


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):

    list_display = ["name", "tag", "number_of_related_datasources", "website"]
    search_fields = ["name", "tag", "website"]
    fields = (
        ("name", "tag"),
        "description",
        "website",
        "countries",
        ("subsidiary_of_1", "subsidiary_of_1_pct"),
        ("subsidiary_of_2", "subsidiary_of_2_pct"),
        ("subsidiary_of_3", "subsidiary_of_3_pct"),
        ("subsidiary_of_4", "subsidiary_of_4_pct"),
        ("date_added", "date_updated"),
    )

    inlines = [DatasourceInline, CommentaryInline]

    def get_queryset(self, request):
        # filter out all but base class
        qs = super(BrandAdmin, self).get_queryset(request).filter(datasource__isnull=True)
        return qs

    def number_of_related_datasources(self, obj):
        """
        Counting the number of data sources is related to.
        """
        related_datasources = obj.bank_brand.all().count()
        return related_datasources

    number_of_related_datasources.short_description = "Nr. Dts"
