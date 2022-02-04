from django.contrib import admin

from .models import Brand


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'tag', 'description']
    search_fields = ['name', 'tag', 'description']
    fields = (
        ('name', 'tag'),
        'description',
        'website',
        'countries',
        'snippet_1',
        'snippet_2',
        'snippet_3',
        ('subsidiary_of_1', 'subsidiary_of_1_pct'),
        ('subsidiary_of_2', 'subsidiary_of_2_pct'),
        ('subsidiary_of_3', 'subsidiary_of_3_pct'),
        ('subsidiary_of_4', 'subsidiary_of_4_pct'),
        ('date_added', 'date_updated'),
    )

    def get_queryset(self, request):
        # filter out all but base class
        qs = super(BrandAdmin, self).get_queryset(request).filter(bank_brand__isnull=False)
        return qs
