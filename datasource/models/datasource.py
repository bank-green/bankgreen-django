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
    suggested_brands = models.ManyToManyField(Brand, related_name="suggested_brands")

    def get_data(self, url, params=None):
        """
        get_data is a generic method that can be used to get data from any data source.
        It is not intended to be used directly.
        """

    @classproperty
    def tag_prepend_str(cls):
        raise NotImplementedError

    def save(self, *args, **kwargs):
        super(Datasource, self).save()
