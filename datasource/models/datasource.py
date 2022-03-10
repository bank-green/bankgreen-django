from django.db import models

from django_countries.fields import CountryField
from Levenshtein import distance as lev

from brand.models import Brand

from ..constants import lev_distance, model_names, read_only_fields


class classproperty(property):
    def __get__(self, obj, objtype=None):
        return super(classproperty, self).__get__(objtype)

    def __set__(self, obj, value):
        super(classproperty, self).__set__(type(obj), value)

    def __delete__(self, obj):
        super(classproperty, self).__delete__(type(obj))


class Datasource(Brand):
    """
    Datasource is the parent of various individual datasources.
    A "Datasource" is never instantiated directly - only as an instance of data from a data provider.
    Sometimes programs make use of the Datasource model, while other times they access the child instance directly
    """

    # Relationships to brand
    # TODO: Read Docs on on_delete and adjust models accordingly
    brand = models.ForeignKey(
        Brand, related_name="bank_brand", null=True, blank=True, on_delete=models.SET_NULL
    )

    # used to identify duplicates on refresh
    source_id = models.CharField(
        max_length=100,
        null=False,
        blank=False,
        editable=True,
        help_text="the original identifier used by the datasource. i.e wikiid, or banktrack tag",
    )
    suggested_brands = models.TextField(blank=True, null=True, default="-blank-")

    def get_data(self, url, params=None):
        """
        get_data is a generic method that can be used to get data from any data source.
        It is not intended to be used directly.
        """

    @classproperty
    def tag_prepend_str(cls):
        return cls.__name__.lower() + "_"

    def brand_suggestions(self):
        """Suggestion of brands based on Levenshtein distance"""
        brand_list = []
        tag_without_cls_name = self.tag[len(self.tag_prepend_str):]
        brand_tags = Brand.objects.filter(datasource__isnull=True).exclude(tag=tag_without_cls_name).values_list("tag", flat=True)

        for tag in brand_tags:
            num = lev(self.tag, tag)
            if num <= lev_distance:
                # this returns all tags, even datasource tags.
                if any(tag.startswith(model) for model in model_names):
                    continue
                brand_list.append(tag)
        brands = ", ".join(brand_list)
        print('ffffffffffffffffffffffffffffffffffffffffffffff', brands)
        app_label = Brand._meta.app_label
        model_name = Brand._meta.model.__name__.lower()
        # return reverse(f"admin:{app_label}_{model_name}_change", )
        from django.utils.html import format_html
        from django.utils.safestring import mark_safe

        suggested_brands = self.suggested_brands.split(',')
        print(suggested_brands, 'yyyyyyyyyyyyyy')
        for str_brand in suggested_brands:
            print(str_brand, type(str_brand))
            # if suggested_brands:
            brand = Brand.objects.get(tag=str_brand)
            # return reverse(f"admin:{app_label}_{model_name}_change", args=(brand.pk,))
            # return mark_safe(
            #     '<img src="%s" style="max-width: 60px; max-height:60px;" />' % self.photo.url
            # )
            return mark_safe(f'<a href="{app_label}/{model_name}/{brand.pk}/change">{brand}</a>')
        # return brands

    # from django.utils.html import format_html
    # def brand_url(self):
    #     app_label = Brand._meta.app_label
    #     model_name = Brand._meta.model.__name__.lower()
    #     # return reverse(f"admin:{app_label}_{model_name}_change", )
    #
    #     suggested_brands = self.suggested_brands.split()
    #     print(suggested_brands, 'yyyyyyyyyyyyyy')
    #     for str_brand in suggested_brands:
    #     # if suggested_brands:
    #         brand = Brand.objects.get(tag=str_brand)
    #         # return reverse(f"admin:{app_label}_{model_name}_change", args=(brand.pk,))
    #
    #         return format_html(f'<a href="{app_label}/{model_name}{brand.pk}/change">zzz</a>')

    def save(self, *args, **kwargs):
        self.suggested_brands = self.brand_suggestions()
        super(Datasource, self).save()
