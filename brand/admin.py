from django.contrib import admin

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


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'tag', 'website']
    list_filter = ('date_updated', 'countries')
    search_fields = ['name', 'tag', 'website']
    fields = (
        ('name', 'tag'),
        'description',
        'website',
        'countries',
        ('subsidiary_of_1', 'subsidiary_of_1_pct'),
        ('subsidiary_of_2', 'subsidiary_of_2_pct'),
        ('subsidiary_of_3', 'subsidiary_of_3_pct'),
        ('subsidiary_of_4', 'subsidiary_of_4_pct'),
        ('date_added', 'date_updated'),
    )
    inlines = (CommentaryInline,)

    def get_queryset(self, request):
        # filter out all but base class
        qs = super(BrandAdmin, self).get_queryset(request).filter(datasource__isnull=True)
        return qs
