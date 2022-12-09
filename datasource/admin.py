from django.contrib import admin
from django.db import models


from django_admin_listfilter_dropdown.filters import ChoiceDropdownFilter, DropdownFilter
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
    list_display = ["name", "source_id"]
    search_fields = ["name", "source_id"]
    list_filter = ("created", "modified", ("countries", ChoiceDropdownFilter))


@admin.register(Banktrack)
class BanktrackAdmin(admin.ModelAdmin):
    list_display = ["name", "tag", "website"]
    search_fields = ["name", "tag", "website"]
    # raw_id_fields = ["subsidiary_of_1", "subsidiary_of_2", "subsidiary_of_3", "subsidiary_of_4", "brand"]
    # autocomplete_fields = ["subsidiary_of_1", "subsidiary_of_2", "subsidiary_of_3", "subsidiary_of_4", "brand"]

    list_filter = (
        "created",
        ("countries", ChoiceDropdownFilter),
        ("brand", admin.EmptyFieldListFilter),
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Don't show all brands. Only those that are not related to other datasources
        """
        if db_field.name == "brand":
            kwargs["queryset"] = Brand.objects.exclude(
                models.Q(tag__startswith="banktrack_")
                | models.Q(tag__startswith="bimpact_")
                | models.Q(tag__startswith="bocc_")
                | models.Q(tag__startswith="fairfinance_")
                | models.Q(tag__startswith="gabv")
                | models.Q(tag__startswith="marketforces_")
                | models.Q(tag__startswith="switchit_")
                | models.Q(tag__startswith="usnic_")
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def extra_field(self, obj):
        pass

    def get_readonly_fields(self, request, obj=None):
        """
        DateTimeField is not completely disabled by get_form(), so we use this method.
        """
        return ["created", "modified"]

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
class BimpactAdmin(DatasourceAdmin, admin.ModelAdmin):
    pass


@admin.register(Bocc)
class BoccAdmin(DatasourceAdmin, admin.ModelAdmin):
    pass


@admin.register(Fairfinance)
class FairfinanceAdmin(DatasourceAdmin, admin.ModelAdmin):
    pass


@admin.register(Gabv)
class GabvAdmin(DatasourceAdmin, admin.ModelAdmin):
    pass


@admin.register(Marketforces)
class MarketforcesAdmin(DatasourceAdmin, admin.ModelAdmin):
    pass


@admin.register(Switchit)
class SwitchitAdmin(DatasourceAdmin, admin.ModelAdmin):
    pass


@admin.register(Usnic)
class UsnicAdmin(DatasourceAdmin, admin.ModelAdmin):
    list_display = ["name", "get_entity_type_display", "rssd", "lei"]
    search_fields = [
        "name",
        "rssd",
        "lei",
        "cusip",
        "aba_prim",
        "fdic_cert",
        "ncua",
        "thrift",
        "thrift_hc",
        "occ",
        "ein",
    ]
    list_filter = (
        "women_or_minority_owned",
        ("country", ChoiceDropdownFilter),
        ("entity_type", DropdownFilter),
        "created",
        "modified",
    )


@admin.register(Wikidata)
class WikidataAdmin(DatasourceAdmin, admin.ModelAdmin):
    pass
