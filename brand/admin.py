from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.urls import reverse
from django.utils.html import escape, format_html

from cities_light.admin import SubRegionAdmin
from cities_light.models import Region, SubRegion
from django_admin_listfilter_dropdown.filters import ChoiceDropdownFilter
from django_countries.fields import Country

from brand.admin_utils import (
    LinkedDatasourcesFilter,
    link_datasources,
    raise_validation_error_for_missing_country,
    raise_validation_error_for_missing_region,
)
from brand.models.brand_update import BrandUpdate
from brand.models.commentary import InstitutionCredential, InstitutionType
from brand.models.features import BrandFeature, FeatureType
from datasource.constants import model_names
from datasource.models.datasource import Datasource, SuggestedAssociation

from .models import Brand, Commentary


class CommentaryInline(admin.StackedInline):
    fk_name = "brand"
    model = Commentary
    autocomplete_fields = ["inherit_brand_rating"]

    readonly_fields = (
        "rating_inherited",
        "from_the_website",
        "subtitle",
        "header",
        "summary",
        "details",
    )
    fieldsets = (
        (
            "Display Configuration",
            {
                "fields": (
                    ("display_on_website", "fossil_free_alliance", "number_of_requests"),
                    ("rating", "show_on_sustainable_banks_page"),
                    ("rating_inherited", "inherit_brand_rating"),
                )
            },
        ),
        ("Used for negatively rated banks", {"fields": (("amount_financed_since_2016",))}),
        (
            "Used for positively rated banks",
            {"fields": (("from_the_website",), ("institution_type", "institution_credentials"))},
        ),
        ("CMS", {"fields": (("subtitle",), ("header",), ("summary",), ("details",))}),
        ("Meta", {"fields": ("comment",)}),
    )


class BrandFeaturesInline(admin.StackedInline):
    model = BrandFeature
    fields = (("feature", "details"),)


# @admin.display(description='Name')
# def upper_case_name(obj):
#     return obj.name.upper()


# TODO make this a series of dropdowns
class DatasourceInline(admin.StackedInline):
    model = Datasource
    extra = 0

    readonly_fields = ("name", "source_id")
    fields = [readonly_fields]

    fk_name = "brand"
    show_change_link = True


class BrandFeaturesReadonlyInline(admin.StackedInline):
    model = BrandFeature
    fields = (("feature", "details"),)
    readonly_fields = ["feature", "details"]


@admin.register(FeatureType)
class BrandFeatureAdmin(admin.ModelAdmin):

    search_fields = ("name", "description")
    list_display = ("name", "description")


class CountriesWidgetOverrideForm(forms.ModelForm):
    description = forms.CharField(widget=forms.Textarea(attrs={"rows": 2, "cols": 100}))
    rssd = forms.CharField(widget=forms.Textarea(attrs={"rows": 1}))
    lei = forms.CharField(widget=forms.Textarea(attrs={"rows": 1}))
    fdic_cert = forms.CharField(widget=forms.Textarea(attrs={"rows": 1}))
    ncua = forms.CharField(widget=forms.Textarea(attrs={"rows": 1}))
    permid = forms.CharField(widget=forms.Textarea(attrs={"rows": 1}))

    def __init__(self, *args, **kwargs):
        super(forms.ModelForm, self).__init__(*args, **kwargs)
        self.fields["description"].required = False
        self.fields["rssd"].required = False
        self.fields["lei"].required = False
        self.fields["fdic_cert"].required = False
        self.fields["ncua"].required = False
        self.fields["permid"].required = False

    class Meta:
        widgets = {
            "countries": FilteredSelectMultiple("countries", is_stacked=False),
            "regions": FilteredSelectMultiple("regions", is_stacked=False),
        }

    def clean(self):
        """
        Checks that all regions have countries associated.
        """
        # raise_validation_error_for_missing_country(self)
        # raise_validation_error_for_missing_region(self)

        return self.cleaned_data


admin.site.unregister(SubRegion)


@admin.register(BrandUpdate)
class BrandUpdateAdmin(admin.ModelAdmin):
    form = CountriesWidgetOverrideForm
    fields = ["brand_link"] + BrandUpdate.UPDATE_FIELDS + ["additional_info", "email", "consent"]
    readonly_fields = ["brand_link", "name", "aliases", "website", "bank_features"]
    inlines = [BrandFeaturesInline]
    autocomplete_fields = ["subregions"]

    list_display = ("short_name", "update_tag", "created", "email", "merged")
    list_filter = ("merged",)

    def brand_link(self, obj):
        """
        Returns a link to the parent Brand object in the admin interface.
        """
        parent_brand = Brand.objects.get(tag=obj.update_tag)
        url = reverse("admin:brand_brand_change", args=(str(parent_brand.pk),))
        return format_html('<a href="{}">{}</a>', url, parent_brand)

    brand_link.short_description = "Brand"

    def save_model(self, request, obj, form, change):
        original = Brand.objects.get(tag=obj.update_tag)

        # overwrite all fields with values from updates
        for field in BrandUpdate.UPDATE_FIELDS:
            if field != "regions" and field != "subregions":
                value = getattr(obj, field)
                setattr(original, field, value)

        # combine country, regions, and subregions
        # if a country or region is not explicitly specified, add it
        combined_subregions = obj.subregions.all() | original.subregions.all()
        original.subregions.set(combined_subregions.distinct())

        combined_regions = (
            obj.regions.all()
            | original.regions.all()
            | Region.objects.filter(id__in=[x.region.id for x in combined_subregions])
        ).distinct()
        original.regions.set(combined_regions)

        implied_countries = set([x.country.code2 for x in combined_regions])
        implied_countries = set([Country(x) for x in implied_countries])

        combined_countries = set(obj.countries).union(implied_countries)
        original.countries = list(combined_countries)

        # It's possible for there to be duplicate feature types.
        # in these cases, delete the original bank features with the same type
        og_features = original.bank_features.all()
        new_features = obj.bank_features.all()

        new_feature_set = set([x.feature for x in new_features])
        intersecting_features = [x.feature for x in og_features if x.feature in new_feature_set]

        for x in intersecting_features:
            og = og_features.filter(feature=x).first()
            og_features = og_features.exclude(id=og.id)

        new_combined_features = og_features | new_features

        original.bank_features.all().delete()
        original.bank_features.set(new_combined_features)

        original.save()

        obj.merged = True
        obj.save()

        # deleting the object results in a an error with regions in forms/models.py _save_m2m
        # and creates a validation error. This has to do with how regions and subregions are configured.
        # It's comented out for now.
        # obj.delete()


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


@admin.register(InstitutionType)
class InstitutionTypes(admin.ModelAdmin):
    model = InstitutionType


@admin.register(InstitutionCredential)
class InstitutionCredentials(admin.ModelAdmin):
    model = InstitutionCredential


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

    search_fields = ["name", "tag", "website"]
    readonly_fields = ["related_datasources", "suggested_associations", "created", "modified"]
    autocomplete_fields = ["subregions"]
    fields = (
        ("name", "tag"),
        ("website", "aliases"),
        ("related_datasources"),
        ("suggested_associations"),
        ("countries"),
        ("regions"),
        ("subregions"),
        ("description"),
        ("rssd", "lei"),
        ("fdic_cert", "ncua"),
        ("permid"),
        # "suggested_datasource",
        ("created", "modified"),
    )

    list_filter = (
        "commentary__display_on_website",
        "commentary__rating",
        "commentary__number_of_requests",
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

    def change_view(self, request, object_id, extra_context=None):
        extra_context = extra_context or {}
        extra_context["page_title"] = f"{Brand.objects.get(id=object_id).tag}: "
        return super(BrandAdmin, self).change_view(request, object_id, extra_context=extra_context)

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["page_title"] = "Brands: "
        return super(BrandAdmin, self).changelist_view(request, extra_context=extra_context)
