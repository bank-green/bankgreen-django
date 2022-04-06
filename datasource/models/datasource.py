from django.db import models

from django_countries.fields import CountryField
from Levenshtein import distance as lev

from brand.models.brand import Brand

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
        tag_without_cls_name = self.tag[len(self.tag_prepend_str) :]
        brand_tags = (
            Brand.objects.filter(datasource__isnull=True)
            .exclude(tag=tag_without_cls_name)
            .values_list("tag", flat=True)
        )
        # print(len(brand_tags), brand_tags)
        for tag in brand_tags:
            num = lev(self.tag, tag)
            if num <= lev_distance:
                # this returns all tags, even datasource tags.
                if any(tag.startswith(model) for model in model_names):
                    continue
                brand_list.append(tag)
        brands = ", ".join(brand_list)
        return brands

    def save(self, *args, **kwargs):
        self.suggested_brands = self.brand_suggestions()
        super(Datasource, self).save()
