from django.contrib import admin
from django.forms import ModelForm
from django.urls import reverse
from django.utils.html import format_html

from datasource.models.datasource import Datasource

from .models import Brand, Commentary

class CommentaryInline(admin.StackedInline):
    model = Commentary
    fieldsets = (
        (
            "Display Configuration",
            {
                "fields": (
                    ("display_on_website", "aliases"),
                    ("rating", "top_three_ethical"),
                    ("recommended_in", "recommended_order"),
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
            {
                "fields": (
                    ("from_the_website",),
                    ("checking_saving_details", "checking_saving"),
                    ("free_checking_details", "free_checking"),
                    ("interest_rates",),
                    ("free_atm_withdrawl_details", "free_atm_withdrawl"),
                    ("local_branches_details", "local_branches", "online_banking"),
                    ("mortgage_or_loan", "deposit_protection"),
                    ("credit_cards_details", "credit_cards"),
                    ("free_international_card_payment",),
                )
            },
        ),
        ("Meta", {"fields": ("comment",)}),
    )

# @admin.display(description='Name')
# def upper_case_name(obj):
#     return obj.name.upper()

class DatasourceInline(admin.StackedInline):
    model = Datasource
    extra = 0
    # raw_id_fields = ["subsidiary_of_2", "subsidiary_of_3", "subsidiary_of_4"]
    fields = ("name",)
    fk_name = "brand"



@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):

    # you are currently attempting to link various datasources inside of a brand.
    # this is achievable by generating an html link via the reverse(function)
    # you are demo-ing with related_darasources
    # uppsercase must be listed both in readonly_fields and in fields
    @admin.display(description='related_darasources')
    def related_darasources(self, obj):
        datasources = Datasource.objects.filter(brand=obj)

        links = []

        banktracks = [x for x in datasources if hasattr(x, "banktrack")]
        for bt in banktracks:
        
            url = reverse('admin:%s_%s_change' % ("datasource", "banktrack"), args=(bt.id,))
            link = f'<a href="{url}" />{bt.name}</a>'
            links.append(link)

        # banktracks = [x for x in datasources if hasattr(x, "banktrack")]
        # bt = banktracks[0]
        # url = reverse('admin:%s_%s_change' % ("datasource", "banktrack"), args=(bt.id,))        
        # names = ", ".join([d.name for d in datasources])
        return ', '.join(links)

    # foo ='bar'
    list_display = ["name", "tag", "number_of_related_datasources", "website"]
    search_fields = ["name", "tag", "website"]
    readonly_fields = ["related_darasources"]
    fields = (
        ("name", "tag", "related_darasources"),
        "description",
        "website",
        "countries",
        ("subsidiary_of_1", "subsidiary_of_1_pct"),
        ("subsidiary_of_2", "subsidiary_of_2_pct"),
        ("subsidiary_of_3", "subsidiary_of_3_pct"),
        ("subsidiary_of_4", "subsidiary_of_4_pct"),
        "suggested_datasource",
        ("date_added", "date_updated"),
    )

    inlines = [
        # CommentaryInline, 
        DatasourceInline]

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
