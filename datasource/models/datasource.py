from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from model_utils.models import TimeStampedModel

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


class Datasource(TimeStampedModel):
    """
    Datasource is the parent of various individual datasources.
    A "Datasource" is never instantiated directly - only as an instance of data from a data provider.
    Sometimes programs make use of the Datasource model, while other times they access the child instance directly
    """

    # Relationships to brand
    brand = models.ForeignKey(
        Brand, related_name="datasources", null=True, blank=True, on_delete=models.SET_NULL
    )
    name = models.CharField(
        "Name of this data source", max_length=200, null=False, blank=False, default="-unnamed-"
    )
    suggested_associations = models.ManyToManyField(
        Brand,
        through="SuggestedAssociation",
        help_text="link between brands and datasources that may be related to eachother",
    )

    # used to identify duplicates on refresh
    source_id = models.CharField(
        max_length=100,
        null=False,
        blank=False,
        editable=True,
        help_text="the original identifier used by the datasource. i.e wikiid, or banktrack tag",
    )
    source_link = models.URLField(
        "Link to the data source's webpage. i.e. the banktrack.org or b-impact webpage for the bank",
        editable=True,
        null=True,
        blank=True,
    )

    def get_data(self, url, params=None):
        """
        get_data is a generic method that can be used to get data from any data source.
        It is not intended to be used directly.
        """

    def save(self, *args, **kwargs):
        super(Datasource, self).save()

    def subclass(self):
        """returns the subclass (i.e. banktrack) that a datasource is."""
        if self.__class__ == Datasource:
            return self
        for model_name in model_names:
            if hasattr(self, model_name):
                return getattr(self, model_name)

        raise NotImplementedError(
            f"{self} is not a Datasource and does not have subclass listed in model_names"
        )


class SuggestedAssociation(models.Model):
    brand = models.ForeignKey(Brand, null=False, on_delete=models.CASCADE)
    datasource = models.ForeignKey(Datasource, null=False, on_delete=models.CASCADE)
    certainty = models.IntegerField(
        default=0,
        validators=[MaxValueValidator(10), MinValueValidator(0)],
        help_text="how certain the system is of this association. 0 is more certain. 10 is least certain.",
    )

    class Meta:
        unique_together = ("brand", "datasource")
