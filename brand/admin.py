from django.contrib import admin
from django.forms import ModelForm
from django.utils.html import format_html

from datasource.models.datasource import Datasource
from django.urls import reverse
from .models import Brand, Commentary


@admin.register(Commentary)
class DatasourceAdmin(admin.ModelAdmin):
    pass


def admin_change_url(obj):
    app_label = obj._meta.app_label
    model_name = obj._meta.model.__name__.lower()
    return reverse("admin:{}_{}_change".format(app_label, model_name), args=(obj.pk,))


def admin_link(attr, short_description, empty_description="-"):
    """Decorator used for rendering a link to a related model in
    the admin detail page.
    attr (str):
        Name of the related field.
    short_description (str):
        Name if the field.
    empty_description (str):
        Value to display if the related field is None.
    The wrapped method receives the related object and should
    return the link text.
    Usage:
        @admin_link('credit_card', _('Credit Card'))
        def credit_card_link(self, credit_card):
            return credit_card.name
    """

    def wrap(func):
        def field_func(self, obj):
            related_obj = getattr(obj, attr)
            if related_obj is None:
                return empty_description
            url = admin_change_url(related_obj)
            return format_html('<a href="{}">{}</a>', url, func(self, related_obj))

        field_func.short_description = short_description
        field_func.allow_tags = True
        return field_func

    return wrap


class CommentaryInline(admin.TabularInline):
    model = Commentary
    extra = 0


class DatasourceInline(admin.TabularInline):
    model = Datasource
    extra = 0
    raw_id_fields = ["subsidiary_of_1", "subsidiary_of_2", "subsidiary_of_3", "subsidiary_of_4"]
    fk_name = "brand"


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):

    list_display = ["name", "commentary_link", "tag", "number_of_related_datasources", "website"]
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

    @admin_link("commentary_brand", "Commentary")
    def commentary_link(self, commentary):
        """Url link for the category of business."""
        """With 20000 posts this decorator increases the list page load from 800 ms to ~3000 ms"""
        return commentary
