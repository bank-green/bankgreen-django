from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.html import escape, format_html

from cities_light.models import Country, Region, SubRegion
from cities_light.admin import SubRegionAdmin

from brand.models.features import BrandFeature, FeatureType
from datasource.constants import model_names
from datasource.models.datasource import Datasource, SuggestedAssociation

from .models import Brand, Commentary

from django_admin_listfilter_dropdown.filters import ChoiceDropdownFilter


class RecommendedInOverrideForm(forms.ModelForm):
    class Meta:
        widgets = {"recommended_in": FilteredSelectMultiple("recommended_in", is_stacked=False)}


class CommentaryInline(admin.StackedInline):
    model = Commentary
    form = RecommendedInOverrideForm
    fieldsets = (
        (
            "Display Configuration",
            {
                "fields": (
                    ("display_on_website", "fossil_free_alliance", "number_of_requests"),
                    ("rating", "fossil_free_alliance_rating", "show_on_sustainable_banks_page"),
                )
            },
        ),
        (
            "READ ONLY text for negatively rated banks. This should be manually migrated to the description field.",
            {
                "fields": (
                    ("snippet_1", "snippet_1_link"),
                    ("snippet_2", "snippet_2_link"),
                    ("snippet_3", "snippet_3_link"),
                )
            },
        ),
        (
            "Text used for positively rated banks",
            {"fields": (("from_the_website",), ("our_take",))},
        ),
        ("CMS", {"fields": (("subtitle",), ("header",), ("summary",), ("details",))}),
        ("Meta", {"fields": ("comment",)}),
    )


class BrandFeaturesInline(admin.StackedInline):
    model = BrandFeature
    fields = (("feature", "offered", "details"),)


# @admin.display(description='Name')
# def upper_case_name(obj):
#     return obj.name.upper()


# TODO make this a series of dropdowns
class DatasourceInline(admin.StackedInline):
    model = Datasource
    extra = 0
    # raw_id_fields = ["subsidiary_of_2", "subsidiary_of_3", "subsidiary_of_4"]
    readonly_fields = ("name", "source_id")
    fields = [readonly_fields]

    fk_name = "brand"
    show_change_link = True


def link_datasources(datasources, datasource_str):
    links = []
    filtered_datasources = [x for x in datasources if hasattr(x, datasource_str)]
    for ds in filtered_datasources:
        url = reverse("admin:%s_%s_change" % ("datasource", datasource_str), args=(ds.id,))
        string_to_show = escape(f"{datasource_str}: {ds.name}")
        link = format_html(f'<a href="{url}" />{string_to_show}</a>')
        links.append(link)
    return links


@admin.register(FeatureType)
class BrandFeatureAdmin(admin.ModelAdmin):

    search_fields = ("name", "description")
    list_display = ("name", "description")


class CountriesWidgetOverrideForm(forms.ModelForm):
    class Meta:
        widgets = {
            "countries": FilteredSelectMultiple("countries", is_stacked=False),
            "regions": FilteredSelectMultiple("regions", is_stacked=False),
        }

    def clean(self):
        """
        Checks that all regions have countries associated.
        """
        raise_validation_error_for_missing_country(self)
        raise_validation_error_for_missing_region(self)

        return self.cleaned_data


def raise_validation_error_for_missing_country(self):
    regions_qs = self.cleaned_data.get("regions", Region.objects.none())
    expected_country_ids = set([x["country_id"] for x in regions_qs.values()])
    expected_country_iso2 = set(
        [x.code2 for x in Country.objects.filter(id__in=expected_country_ids)]
    )

    actual_countries_iso2 = set([x for x in self.cleaned_data.get("countries", [])])
    # validation hack for when datasources don't have "countries" defined, but only "country"
    if single_country := self.cleaned_data.get("country"):
        actual_countries_iso2.add(single_country)

    if not expected_country_iso2.issubset(actual_countries_iso2):
        missing_country_codes = expected_country_iso2 - actual_countries_iso2
        missing_country_names = ", ".join(
            [x.name for x in Country.objects.filter(code2__in=missing_country_codes)]
        )

        raise ValidationError(
            f"All regions must have associated countries. The following countries are missing: {missing_country_names}"
        )


def raise_validation_error_for_missing_region(self):
    regions_qs = self.cleaned_data.get("regions", Region.objects.none())
    subregions_qs = self.cleaned_data.get("subregions", SubRegion.objects.none())
    expected_regions = set([x.region for x in subregions_qs])

    if not expected_regions.issubset(set(regions_qs)):
        missing_regions = expected_regions - set(regions_qs)
        missing_region_names = " | ".join([x.display_name for x in missing_regions])

        raise ValidationError(
            f"All subregions must have associated regions. The following subregions are missing: {missing_region_names}"
        )


class SubRegionAdminOverride(SubRegionAdmin):
    search_fields = SubRegionAdmin.search_fields + (
        "country__name",
        "country__name_ascii",
        "region__name",
        "region__name_ascii",
    )  # type: ignore


admin.site.unregister(SubRegion)
admin.site.register(SubRegion, SubRegionAdminOverride)


class LinkedDatasourcesFilter(admin.SimpleListFilter):
    title = "Linked Datasources"
    parameter_name = "Linked Datasources"

    def lookups(self, request, model_admin):
        return (("Linked", "Linked"), ("Unlinked", "Unlinked"))

    def queryset(self, request, queryset):
        value = self.value()
        if value == "Linked":
            brand_pks = [x.brand.pk for x in Datasource.objects.filter(brand__isnull=False)]
            return queryset.filter(pk__in=brand_pks)
        if value == "Unlinked":
            brand_pks = [x.brand.pk for x in Datasource.objects.filter(brand__isnull=False)]
            return queryset.exclude(pk__in=brand_pks)
        return queryset


class HasSuggestionsFilter(admin.SimpleListFilter):
    title = "suggested associations"
    parameter_name = "suggested associations"

    def lookups(self, request, model_admin):
        return (
            ("Any Suggestions", "Any Suggestions"),
            ("No Suggestions", "No Suggestions"),
            ("High Certainty Suggestions", "High Certainty Suggestions"),
            (" Medium Certainty Suggestions", " Medium Certainty Suggestions"),
            (" Low Certainty Suggestions", " Low Certainty Suggestions"),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == "Any Suggestions":
            brand_pks = [x.brand.pk for x in SuggestedAssociation.objects.all()]
            return queryset.filter(pk__in=brand_pks)
        if value == "No Suggestions":
            brand_pks = [x.brand.pk for x in SuggestedAssociation.objects.all()]
            return queryset.exclude(pk__in=brand_pks)
        elif value == "High Certainty Suggestions":
            brand_pks = [x.brand.pk for x in SuggestedAssociation.objects.filter(certainty__lte=3)]
            return queryset.filter(pk__in=brand_pks)
        elif value == " Medium Certainty Suggestions":
            brand_pks = [
                x.brand.pk
                for x in SuggestedAssociation.objects.filter(certainty__gte=4, certainty__lte=7)
            ]
            return queryset.filter(pk__in=brand_pks)
        elif value == " Low Certainty Suggestions":
            brand_pks = [
                x.datasource.pk for x in SuggestedAssociation.objects.filter(certainty__gte=8)
            ]
            return queryset.filter(pk__in=brand_pks)
        return queryset


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    form = CountriesWidgetOverrideForm

    @admin.display(description="related datasources")
    def related_datasources(self, obj):
        datasources = obj.datasources.all()
        links = []
        for model in model_names:
            links += link_datasources(datasources, model)
        return format_html("<br />".join(links))

    @admin.display(description="suggested associations")
    def suggested_associations(self, obj):
        suggested_associations = SuggestedAssociation.objects.filter(brand=obj)
        datasources = [x.datasource for x in suggested_associations]
        links = []
        for model in model_names:
            links += link_datasources(datasources, model)
        return format_html("<br />".join(links))

    def num_suggest(self, obj):
        num = SuggestedAssociation.objects.filter(brand=obj).count()
        return str(num) if num else ""

    def num_linked(self, obj):
        num = obj.datasources.count()
        return str(num) if num else ""

    raw_id_fields = ["subsidiary_of_1", "subsidiary_of_2", "subsidiary_of_3", "subsidiary_of_4"]
    search_fields = ["name", "tag", "website"]
    readonly_fields = ["related_datasources", "suggested_associations", "created", "modified"]
    autocomplete_fields = ["subregions"]
    fields = (
        ("name", "tag"),
        ("website", "aliases"),
        ("related_datasources"),
        ("suggested_associations"),
        ("description"),
        ("countries"),
        ("regions"),
        ("subregions"),
        ("rssd", "rssd_locked"),
        ("lei", "lei_locked"),
        ("permid", "permid_locked"),
        ("ncua", "ncua_locked"),
        ("fdic_cert", "fdic_cert_locked"),
        # ("subsidiary_of_1", "subsidiary_of_1_pct"),
        # ("subsidiary_of_2", "subsidiary_of_2_pct"),
        # ("subsidiary_of_3", "subsidiary_of_3_pct"),
        # ("subsidiary_of_4", "subsidiary_of_4_pct"),
        # "suggested_datasource",
        ("created", "modified"),
    )
    list_filter = (
        "commentary__display_on_website",
        "commentary__rating",
        "commentary__number_of_requests",
        "commentary__top_three_ethical",
        HasSuggestionsFilter,
        LinkedDatasourcesFilter,
        ("countries", ChoiceDropdownFilter),
    )
    list_display = ("short_name", "short_tag", "pk", "website", "num_suggest", "num_linked")
    list_per_page = 800

    inlines = [DatasourceInline, CommentaryInline, BrandFeaturesInline]

    def get_queryset(self, request):
        # filter out all but base class
        qs = super(BrandAdmin, self).get_queryset(request)
        return qs

    def number_of_related_datasources(self, obj):
        """
        Counting the number of data sources is related to.
        """
        related_datasources = obj.datasources.all().count()
        return related_datasources

    number_of_related_datasources.short_description = "Nr. Dts"
