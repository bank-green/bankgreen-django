from django.contrib import admin
from django.db import models

from django_admin_listfilter_dropdown.filters import (
    ChoiceDropdownFilter,
    DropdownFilter,
    RelatedDropdownFilter,
)
from Levenshtein import distance as lev

from brand.models import Brand

from .constants import lev_distance, model_names, read_only_fields
from .models import (
    Banktrack,
    Bimpact,
    Bocc,
    Datasource,
    Fairfinance,
    Gabv,
    Marketforces,
    Switchit,
    Usnic,
    Wikidata,
)


@admin.register(Datasource)
class DatasourceAdmin(admin.ModelAdmin):
    list_display = ["name", "tag", "website", "brand"]
    search_fields = ["name", "tag", "website"]
    list_filter = (
        "date_added",
        ("countries", ChoiceDropdownFilter),
        ("brand", admin.EmptyFieldListFilter),
    )


@admin.register(Banktrack)
class BanktrackAdmin(admin.ModelAdmin):
    list_display = ["name", "tag", "website", "brand"]
    search_fields = ["name", "tag", "website"]
    list_filter = (
        "date_added",
        ("countries", ChoiceDropdownFilter),
        ("brand", admin.EmptyFieldListFilter),
    )

    def extra_field(self, obj):
        pass

    def get_readonly_fields(self, request, obj=None):
        """
        DateTimeField is not completely disabled by get_form(), so we use this method.
        """
        return ["date_added", "date_updated"]

    def get_form(self, request, obj=None, **kwargs):
        """
        This is used to disable fields, so the user can't change its value
        """
        form = super().get_form(request, obj, **kwargs)
        disabled_fields = set()
        disabled_fields |= read_only_fields

        for f in disabled_fields:
            if f in form.base_fields:
                form.base_fields[f].disabled = True
        return form


@admin.register(Bimpact)
class BimpactAdmin(BanktrackAdmin, admin.ModelAdmin):
    pass


@admin.register(Bocc)
class BoccAdmin(BanktrackAdmin, admin.ModelAdmin):
    pass


@admin.register(Fairfinance)
class FairfinanceAdmin(BanktrackAdmin, admin.ModelAdmin):
    pass


@admin.register(Gabv)
class GabvAdmin(BanktrackAdmin, admin.ModelAdmin):
    pass


@admin.register(Marketforces)
class MarketforcesAdmin(BanktrackAdmin, admin.ModelAdmin):
    pass


@admin.register(Switchit)
class SwitchitAdmin(BanktrackAdmin, admin.ModelAdmin):
    pass


# @admin.register(Usnic)
# class UsnicAdmin(BanktrackAdmin, admin.ModelAdmin):
#     pass
#
#
# @admin.register(Wikidata)
# class WikidataAdmin(BanktrackAdmin, admin.ModelAdmin):
#     pass
