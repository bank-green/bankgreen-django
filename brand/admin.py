from django.contrib import admin
from django.urls import reverse
from django.utils.html import escape, format_html
from brand.models.features import Features

from datasource.constants import model_names
from datasource.models.datasource import Datasource

from .models import Brand, Commentary


class CommentaryInline(admin.StackedInline):
    model = Commentary
    fieldsets = (
        (
            "Display Configuration",
            {
                "fields": (
                    ("display_on_website",),
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
                )
            },
        ),
        (
            "Text used for positively rated banks",
            {"fields": (("from_the_website",), ("our_take",))},
        ),
        ("Meta", {"fields": ("comment",)}),
    )


class FeaturesInline(admin.StackedInline):
    model = Features
    fields = (
        ("checking_saving_details", "checking_saving"),
        ("free_checking_details", "free_checking"),
        ("interest_rates",),
        ("free_atm_withdrawal_details", "free_atm_withdrawal"),
        ("local_branches_details", "local_branches", "online_banking"),
        ("mortgage_or_loan", "deposit_protection"),
        ("credit_cards_details", "credit_cards"),
        ("free_international_card_payment",),
    )


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


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
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

    inlines = [DatasourceInline, CommentaryInline, FeaturesInline]

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
