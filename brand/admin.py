from django.contrib import admin
from django.forms import ModelForm
from django.utils.html import format_html
from datasource.models.datasource import Datasource
from django.urls import reverse
from .models import Brand, Commentary


class CommentaryInline(admin.StackedInline):
    model = Commentary
    fieldsets = (
        (
            'Display Configuration',
            {
                'fields': (
                    ('display_on_website', 'aliases'),
                    ('rating', 'top_three_ethical'),
                    ('recommended_in', 'recommended_order'),
                )
            },
        ),
        (
            'Text used for both positively and negatively rated banks',
            {'fields': ('headline', 'top_blurb_headline', 'top_blurb_subheadline')},
        ),
        (
            'Text used for negatively rated banks',
            {
                'fields': (
                    ('snippet_1', 'snippet_1_link'),
                    ('snippet_2', 'snippet_2_link'),
                    ('snippet_3', 'snippet_3_link'),
                )
            },
        ),
        (
            'Text used for positively rated banks',
            {
                'fields': (
                    ('from_the_website',),
                    ('checking_saving_details', 'checking_saving'),
                    ('free_checking_details', 'free_checking'),
                    ('interest_rates',),
                    ('free_atm_withdrawl_details', 'free_atm_withdrawl'),
                    ('local_branches_details', 'local_branches', 'online_banking'),
                    ('mortgage_or_loan', 'deposit_protection'),
                    ('credit_cards_details', 'credit_cards'),
                    ('free_international_card_payment',),
                )
            },
        ),
        ('Meta', {'fields': ('comment',)}),
    )


# class CommentaryInline(admin.StackedInline):
#     model = Commentary
#     extra = 0


class DatasourceInline(admin.TabularInline):
    model = Datasource
    extra = 0
    raw_id_fields = ["subsidiary_of_1", "subsidiary_of_2", "subsidiary_of_3", "subsidiary_of_4"]
    fk_name = "brand"


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_filter = ('date_updated', 'countries')
    list_display = ["name", "tag", "number_of_related_datasources", "website"]
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

    inlines = [DatasourceInline, CommentaryInline]

    def get_queryset(self, request):
        # filter out all but base class
        qs = super(BrandAdmin, self).get_queryset(request).filter(datasource__isnull=True)
        return qs

    def number_of_related_datasources(self, obj):
        """
        Counting the number of data sources is related to.
        """
        related_datasources = obj.bank_brand.all().count()
        return related_datasources

    number_of_related_datasources.short_description = "Nr. Dts"
