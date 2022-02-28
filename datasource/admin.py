from django.contrib import admin

from .models import (
    Banktrack,
    Bimpact,
    Bocc,
    Fairfinance,
    Gabv,
    Marketforces,
    Switchit,
    Usnic,
    Wikidata,
    Datasource
)


@admin.register(
    Banktrack, Bimpact, Bocc, Fairfinance, Gabv, Marketforces, Switchit, Usnic, Wikidata
)

@admin.register(Datasource)
class DatasourceAdmin(admin.ModelAdmin):
    # a list of displayed columns name.
    list_display = ["name", "tag", "website"]
    search_fields = ["name", "tag", "website"]
