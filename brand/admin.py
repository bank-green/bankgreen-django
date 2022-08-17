from django import forms
from django.contrib import admin
from django.urls import reverse
from django.utils.html import escape, format_html

from brand.models.features import BrandFeature, FeatureType
from datasource.constants import model_names
from datasource.models.datasource import Datasource

from .models import Brand, Commentary

from django.contrib.admin.widgets import FilteredSelectMultiple

from django.db import models


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
                    ("rating", "top_three_ethical"),
                    ("recommended_in"),
                    ("result_page_variation"),
                )
            },
        ),
        (
            "Text used for both positively and negatively rated banks",
            {"fields": ("headline", "top_blurb_headline", "top_blurb_subheadline")},
        ),
        (
            "Text used for negatively rated banks",
            {
                "fields": (
                    ("snippet_1", "snippet_1_link"),
                    ("snippet_2", "snippet_2_link"),
                    ("snippet_3", "snippet_3_link"),
                    ("amount_financed_since_2016"),
                )
            },
        ),
        (
            "Text used for positively rated banks",
            {"fields": (("from_the_website",), ("our_take",))},
        ),
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


@admin.register(FeatureType)
class BrandFeatureAdmin(admin.ModelAdmin):

    search_fields = ("name", "description")
    list_display = ("name", "description")


class CountriesWidgetOverrideForm(forms.ModelForm):
    class Meta:
        widgets = {"countries": FilteredSelectMultiple("countries", is_stacked=False)}


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    form = CountriesWidgetOverrideForm

    @admin.display(description="related_datasources")
    def related_datasources(self, obj):
        datasources = obj.datasources.all()
        links = []
        for model in model_names:
            links += link_datasources(datasources, model)
        return format_html("<br />".join(links))

    raw_id_fields = ["subsidiary_of_1", "subsidiary_of_2", "subsidiary_of_3", "subsidiary_of_4"]
    # list_display = ["name", "tag", "number_of_related_datasources", "website"]
    search_fields = ["name", "tag", "website"]
    readonly_fields = ["related_datasources", "created", "modified"]
    fields = (
        ("name", "name_locked"),
        ("tag", "tag_locked"),
        ("aliases"),
        ("related_datasources"),
        ("description", "description_locked"),
        ("website", "website_locked"),
        ("countries"),
        ("subsidiary_of_1", "subsidiary_of_1_pct"),
        ("subsidiary_of_2", "subsidiary_of_2_pct"),
        ("subsidiary_of_3", "subsidiary_of_3_pct"),
        ("subsidiary_of_4", "subsidiary_of_4_pct"),
        # "suggested_datasource",
        ("created", "modified"),
    )
    list_filter = (
        "commentary__display_on_website",
        "commentary__rating",
        "commentary__number_of_requests",
        "commentary__top_three_ethical",
    )
    list_display = ("short_name", "short_tag", "website")
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
