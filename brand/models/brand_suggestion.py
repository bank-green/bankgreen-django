from datetime import datetime
from django.db import models
from model_utils.models import TimeStampedModel
from django.template.defaultfilters import truncatechars

from cities_light.models import Region, SubRegion
from django_countries.fields import CountryField


class BrandSuggestion(TimeStampedModel):
    """
        This is the extension of the Brand container with the additional parameters.
    """
    name = models.CharField(
        "Name of this brand", max_length=200, null=False, blank=False, default="-unnamed-"
    )

    @property
    def short_name(self):
        return truncatechars(self.name, 50)

    @property
    def short_tag(self):
        return truncatechars(self.tag, 50)

    name_locked = models.BooleanField(default=False)
    aliases = models.CharField(
        help_text="Other names for the brand, used for search. comma seperated. i.e. BOFA, BOA",
        max_length=200,
        null=True,
        blank=True,
    )
    description = models.TextField(
        "Description of this instance of this brand", null=True, blank=True, default=""
    )
    description_locked = models.BooleanField(default=False)
    website = models.URLField(
        "Website of this brand. i.e. bankofamerica.com", null=True, blank=True
    )
    website_locked = models.BooleanField(default=False)
    countries = CountryField(
        multiple=True, help_text="Where the brand offers retails services", blank=True
    )
    regions = models.ManyToManyField(
        Region, blank=True, help_text="regions in which there are local branches of a bank"
    )
    subregions = models.ManyToManyField(
        SubRegion, blank=True, help_text="regions in which there are local branches of a bank"
    )

    tag = models.CharField(
        max_length=100,
        null=False,
        blank=False,
        editable=True,
        unique=True,
        help_text="the tag we use or this brand record at Bank.Green. ",
    )
    tag_locked = models.BooleanField(default=True)
    submitter_name = models.CharField(verbose_name="Name of the submitter", max_length=100, null=False,
                                      blank=False, default='unnamed')

    submitter_email = models.EmailField("Email of the submitter", max_length=100, blank=True)

    submission_date = models.DateTimeField(default=datetime.now, blank=True)

    class Meta:
        verbose_name_plural = "Brand suggestions"
