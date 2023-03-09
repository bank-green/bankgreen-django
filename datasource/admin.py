from django.contrib import admin, messages
from django.db import models
from django.urls import reverse
from django.utils.html import escape, format_html

from django_admin_listfilter_dropdown.filters import ChoiceDropdownFilter, DropdownFilter

# from django_json_widget.widgets import JSONEditorWidget

# from jsonfield import JSONField

from brand.admin import CountriesWidgetOverrideForm
from brand.models import Brand
from datasource.models.datasource import SuggestedAssociation
from datasource.models.usnic import EntityTypes

# from .constants import lev_distance, model_names
from .constants import read_only_fields
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


class IsLinkedToBrandFilter(admin.SimpleListFilter):
    title = "linked to brand"
    parameter_name = "linked to brand"

    def lookups(self, request, model_admin):
        return (("Linked", "Linked"), ("Not Linked", "Not Linked"))

    def queryset(self, request, queryset):
        value = self.value()
        if value == "Linked":
            return queryset.filter(brand__isnull=False)
        elif value == "Not Linked":
            return queryset.filter(brand__isnull=True)
        return queryset


class IsControlledFilter(admin.SimpleListFilter):
    title = "controlled"
    parameter_name = "controlled"

    def lookups(self, request, model_admin):
        return (("Independent", "Independent"), ("Controlled", "Controlled"))

    def queryset(self, request, queryset):
        value = self.value()
        if value == "Independent":
            return queryset.filter(control__iexact="{}")
        elif value == "Controlled":
            return queryset.exclude(control__iexact="{}")
        return queryset


class HasRegionalBranchesFilter(admin.SimpleListFilter):
    title = "regional branches"
    parameter_name = "regional branches"

    def lookups(self, request, model_admin):
        return (("Branches", "Branches"), ("No Branches", "No Branches"))

    def queryset(self, request, queryset):
        value = self.value()
        if value == "Branches":
            return queryset.exclude(regions=None)
        elif value == "No Branches":
            return queryset.filter(regions=None)
        return queryset


class HasSuggestedAssociationsFilter(admin.SimpleListFilter):
    title = "suggested associations"
    parameter_name = "suggested associations"

    def lookups(self, request, model_admin):
        return (
            ("No Suggestions", "No Suggestions"),
            ("Any Suggestions", "Any Suggestions"),
            ("High Certainty Suggestions", "High Certainty Suggestions"),
            (" Medium Certainty Suggestions", " Medium Certainty Suggestions"),
            (" Low Certainty Suggestions", " Low Certainty Suggestions"),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == "No Suggestions":
            return queryset.filter(suggested_associations=None)
        if value == "Any Suggestions":
            return queryset.exclude(suggested_associations=None)
        elif value == "High Certainty Suggestions":
            # assocs = [x.brand for x in SuggestedAssociation.objects.filter(certainty=0)]
            usnic_pks = [
                x.datasource.pk for x in SuggestedAssociation.objects.filter(certainty__lte=3)
            ]
            return queryset.filter(pk__in=usnic_pks)
        elif value == " Medium Certainty Suggestions":
            usnic_pks = [
                x.datasource.pk
                for x in SuggestedAssociation.objects.filter(certainty__gte=4, certainty__lte=7)
            ]
            return queryset.filter(pk__in=usnic_pks)
        elif value == " Low Certainty Suggestions":
            usnic_pks = [
                x.datasource.pk for x in SuggestedAssociation.objects.filter(certainty__gte=8)
            ]
            return queryset.filter(pk__in=usnic_pks)
        return queryset


@admin.register(Datasource)
class DatasourceAdmin(admin.ModelAdmin):
    list_display = ["name", "source_id"]
    search_fields = ["name", "source_id"]
    list_filter = ["created", "modified"]

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["page_title"] = f"{self.model.__name__}: "

        if hasattr(self.model, "countries"):
            self.list_filter = self.list_filter + [("countries", ChoiceDropdownFilter)]  # type: ignore

        return super(DatasourceAdmin, self).changelist_view(request, extra_context=extra_context)


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

    def change_view(self, request, object_id, extra_context=None):
        extra_context = extra_context or {}
        model_name = self.model.__name__
        datasource_name = Banktrack.objects.get(id=object_id).name
        extra_context["page_title"] = f"{model_name}: {datasource_name}: "
        return super(BanktrackAdmin, self).change_view(
            request, object_id, extra_context=extra_context
        )


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
    form = CountriesWidgetOverrideForm

    actions = ['add_to_Brands']

    @admin.action(description='Create new related Brand and copy data')
    def add_to_Brands(self, request, queryset):
        self.message_user(request, 'Test Successful', messages.SUCCESS)

    def branch_regions(self, obj):
        return ", ".join([x["geoname_code"] for x in obj.regions.values()])

    def num_suggest(self, obj):
        num = SuggestedAssociation.objects.filter(datasource=obj).count()
        return str(num) if num else ""

    list_display = [
        "name",
        "branch_regions",
        "num_suggest",
        "get_entity_type_display",
        "pk",
        "rssd",
        "lei",
    ]
    search_fields = [
        "name",
        "legal_name",
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
        ("regions__name", DropdownFilter),
        ("entity_type", DropdownFilter),
        IsLinkedToBrandFilter,
        HasRegionalBranchesFilter,
        HasSuggestedAssociationsFilter,
        IsControlledFilter,
        "created",
        "modified",
    )

    @admin.display(description="controlling orgs")
    def controlling_orgs(self, obj):
        controlling_rssds = list(obj.control.keys())
        controlling_orgs = Usnic.objects.filter(rssd__in=controlling_rssds)
        html = ""
        for controller in controlling_orgs:
            url = reverse("admin:%s_%s_change" % ("datasource", "usnic"), args=(controller.pk,))
            html += f"<a href='{url}'>{controller.name} - rssd:{controller.rssd} - id:{controller.pk}</a><br />"
        return format_html(html)

    @admin.display(description="suggested_brands")
    def suggested_brands(self, obj):
        associations = SuggestedAssociation.objects.filter(datasource=obj)
        associations.order_by("certainty")
        html = "<p>The system is more sure of some likely associations than others. Banks with short names often result in poor matches. 0 is most certain. 10 is least certain.</p>"
        for assoc in associations:
            url = reverse("admin:%s_%s_change" % ("brand", "brand"), args=(assoc.brand.pk,))
            html += f"<a href='{url}'>{assoc.brand.tag} - {assoc.brand.pk} - {assoc.brand.name} | certainty: {assoc.certainty}</a> <br />"
        return format_html(html)

    @admin.display(description="entity type")
    def entity_type_override(self, obj):
        return f"{obj.entity_type}: {EntityTypes[obj.entity_type].value}"

    fields = (
        ("name", "legal_name", "website", "women_or_minority_owned"),
        "suggested_brands",
        "brand",
        ("rssd", "lei", "source_id"),
        ("entity_type_override"),
        ("country"),
        ("regions", "subregions"),
        "controlling_orgs",
        ("control"),
        ("cusip", "aba_prim", "fdic_cert", "ncua", "thrift", "thrift_hc", "occ", "ein"),
    )

    readonly_fields = ("controlling_orgs", "entity_type_override", "suggested_brands")

    # formfield_overrides = {JSONField: {"widget": JSONEditorWidget}}
    autocomplete_fields = ["brand"]

    def change_view(self, request, object_id, extra_context=None):
        extra_context = extra_context or {}
        model_name = self.model.__name__
        datasource_name = Usnic.objects.get(id=object_id).name
        extra_context["page_title"] = f"{model_name}: {datasource_name}: "
        return super(UsnicAdmin, self).change_view(request, object_id, extra_context=extra_context)


@admin.register(Wikidata)
class WikidataAdmin(DatasourceAdmin, admin.ModelAdmin):
    pass
