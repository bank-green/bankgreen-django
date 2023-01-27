from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.urls import reverse
from django.utils.html import escape, format_html

from cities_light.admin import SubRegionAdmin
from cities_light.models import SubRegion
from django_admin_listfilter_dropdown.filters import ChoiceDropdownFilter

from brand.admin_utils import (
    LinkedDatasourcesFilter,
    link_datasources,
    raise_validation_error_for_missing_country,
    raise_validation_error_for_missing_region,
)
from brand.models.brand_update import BrandUpdate
from brand.models.features import BrandFeature, FeatureType
from datasource.constants import model_names
from datasource.models.datasource import Datasource, SuggestedAssociation

from .models import Brand, Commentary


class RecommendedInOverrideForm(forms.ModelForm):
    class Meta:
        widgets = {"recommended_in": FilteredSelectMultiple("recommended_in", is_stacked=False)}


class CommentaryInline(admin.StackedInline):
    fk_name = "brand"
    model = Commentary
    form = RecommendedInOverrideForm

    readonly_fields = ("rating_inherited",)
    fieldsets = (
        (
            "Display Configuration",
            {
                "fields": (
                    ("display_on_website", "fossil_free_alliance", "number_of_requests"),
                    ("rating", "fossil_free_alliance_rating", "show_on_sustainable_banks_page"),
                    ("rating_inherited", "inherit_brand_rating"),
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
        url = reverse("admin:%s_%s_change" % ("datasource", "banktrack"), args=(ds.id,))
        string_to_show = escape(f"{datasource_str} - . - . - {ds.name}")
        link = format_html(f'<a href="{url}" />{string_to_show}</a>')
        links.append(link)
    return links


class BrandFeaturesReadonlyInline(admin.StackedInline):
    model = BrandFeature
    fields = (("feature", "offered", "details"),)
    readonly_fields = ["feature", "offered", "details"]


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


admin.site.unregister(SubRegion)


@admin.register(BrandUpdate)
class BrandUpdateAdmin(admin.ModelAdmin):
    form = CountriesWidgetOverrideForm
    fields = BrandUpdate.UPDATE_FIELDS
    readonly_fields = ["name", "aliases", "description", "website", "bank_features"]
    inlines = [BrandFeaturesReadonlyInline]
    list_display = ("short_name", "update_tag")

    def save_model(self, request, obj, form, change):
        original = Brand.objects.get(tag=obj.update_tag)

        # overwrite all fields with values from updates
        for field in BrandUpdate.UPDATE_FIELDS:
            value = getattr(obj, field)
            setattr(original, field, value)

        # overwrite features with features from update
        BrandFeature.objects.filter(brand=original).delete()
        original.bank_features.set(obj.bank_features.all())

        original.save()

        # delete brand update
        obj.delete()


@admin.register(SubRegion)
class SubRegionAdminOverride(SubRegionAdmin):
    search_fields = SubRegionAdmin.search_fields + (
        "country__name",
        "country__name_ascii",
        "region__name",
        "region__name_ascii",
    )  # type: ignore


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
        datasources = obj.datasources.filter(brand=obj)
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

    @admin.display(ordering="-commentary__number_of_requests")
    def num_requests(self, obj):
        num_requests = obj.commentary.number_of_requests
        return "-" if not num_requests else num_requests

    @admin.display(ordering="tag")
    def tag(self, obj):
        return obj.tag

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
    list_display = (
        "short_name",
        "short_tag",
        "num_requests",
        "pk",
        "website",
        "num_linked",
        "num_suggest",
    )
    list_display_links = ("short_name", "short_tag")
    # list_editable=('website',)

    list_per_page = 800

    inlines = [CommentaryInline, BrandFeaturesInline, DatasourceInline]

    def get_queryset(self, request):
        # filter out all but base class
        qs = super(BrandAdmin, self).get_queryset(request).filter(brandupdate__isnull=True)
        return qs

    def number_of_related_datasources(self, obj):
        """
        Counting the number of data sources is related to.
        """
        related_datasources = obj.datasources.all().count()
        return related_datasources

    number_of_related_datasources.short_description = "Nr. Dts"
