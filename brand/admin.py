from django.contrib import admin

from datasource.models.datasource import Datasource
from .models import Brand


class CompanyEmployeeInline(admin.TabularInline):
    model = Datasource
    extra = 0
    # raw_id_fields = ["user"]
    # fk_name = ''


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ["name", "tag", "website"]
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

    # inlines = [CompanyEmployeeInline]

    def get_queryset(self, request):
        # filter out all but base class
        qs = super(BrandAdmin, self).get_queryset(request).filter(datasource__isnull=True)
        return qs
