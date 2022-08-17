from typing import List, Tuple

from django.db import models
from django.template.defaultfilters import truncatechars
from django.utils import timezone

from django_countries.fields import CountryField
from cities_light.models import Region
from model_utils.models import TimeStampedModel

import datasource.models as dsm
from datasource.constants import lev_distance, model_names


# from Levenshtein import distance as lev


class Brand(TimeStampedModel):
    """
    A "Brand" is the instance shown to the end user.
    Multiple Datasources may be associated with a single brand.
    The brand's charasterics are initially determined by the data sources.
    However, they may be overwritten by the user.
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
    regions = models.ManyToManyField(Region)
    tag = models.CharField(
        max_length=100,
        null=False,
        blank=False,
        editable=True,
        unique=True,
        help_text=("the tag we use or this brand record at Bank.Green. ",),
    )
    tag_locked = models.BooleanField(default=True)

    # unique identifiers
    # These are all institutional identifiers of this entity
    permid = models.CharField(max_length=15, blank=True)
    permid_locked = models.BooleanField(default=False)
    isin = models.CharField(max_length=15, blank=True)
    isin_locked = models.BooleanField(default=False)
    viafid = models.CharField(max_length=15, blank=True)
    viafid_locked = models.BooleanField(default=False)
    lei = models.CharField(max_length=15, blank=True)
    lei_locked = models.BooleanField(default=False)
    googleid = models.CharField(max_length=15, blank=True)
    googleid_locked = models.BooleanField(default=False)
    rssd = models.CharField(max_length=15, blank=True)
    rssd_locked = models.BooleanField(default=False)
    rssd_hd = models.CharField(max_length=15, blank=True)
    rssd_hd_locked = models.BooleanField(default=False)
    cusip = models.CharField(max_length=15, blank=True)
    cusip_locked = models.BooleanField(default=False)
    thrift = models.CharField(max_length=15, blank=True)
    thrift_locked = models.BooleanField(default=False)
    thrift_hc = models.CharField(max_length=15, blank=True)
    thrift_hc_locked = models.BooleanField(default=False)
    aba_prim = models.CharField(max_length=15, blank=True)
    aba_prim_locked = models.BooleanField(default=False)
    ncua = models.CharField(max_length=15, blank=True)
    ncua_locked = models.BooleanField(default=False)
    fdic_cert = models.CharField(max_length=15, blank=True)
    fdic_cert_locked = models.BooleanField(default=False)
    occ = models.CharField(max_length=15, blank=True)
    occ_locked = models.BooleanField(default=False)
    ein = models.CharField(max_length=15, blank=True)
    ein_locked = models.BooleanField(default=False)

    # subsidiary information. Subsidiaries should be listed in descending order of ownership
    # i.e. a DataSource A wholly owned by DataSource B would have subsidiary_of_1 set to B, and
    # subsidiary_of_1_pct set to 100
    subsidiary_of_1 = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        related_name="subsidiary_of_1_data_source",
        blank=True,
    )
    subsidiary_of_1_pct = models.IntegerField("percentage owned by subsidiary 1", default=0)
    subsidiary_of_2 = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        related_name="subsidiary_of_2_data_source",
        blank=True,
    )
    subsidiary_of_2_pct = models.IntegerField("percentage owned by subsidiary 2", default=0)
    subsidiary_of_3 = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        related_name="subsidiary_of_3_data_source",
        blank=True,
    )
    subsidiary_of_3_pct = models.IntegerField("percentage owned by subsidiary 3", default=0)
    subsidiary_of_4 = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        related_name="subsidiary_of_4_data_source",
        blank=True,
    )
    subsidiary_of_4_pct = models.IntegerField("percentage owned by subsidiary 4", default=0)

    def __str__(self):
        return self.tag

    def __repr__(self):
        return f"<{type(self).__name__}: {self.tag}>"

    def refresh_name(self, overwrite_existing=False):
        # if the existing name is the default, we are overwriting
        # otherwise, we're not doing anything.
        if self.name == self.__class__.name.field.default:
            overwrite_existing = True
        if overwrite_existing is False:
            return self.name, self.name

        old_name = self.name
        new_name = old_name

        # Favor Banktrack names
        if banktrack_datasources := dsm.Banktrack.objects.filter(brand=self):
            if len(banktrack_datasources) > 0:
                new_name = banktrack_datasources[0].name
                self.name = new_name
                self.save()
                return (old_name, new_name)
        elif wikidata_datasources := dsm.Wikidata.objects.filter(brand=self):
            if len(wikidata_datasources) > 0:
                new_name = wikidata_datasources[0].name
                self.name = new_name
                self.save()

        return (old_name, new_name)

    # TODO: Figure out how I can deduplicate these refreshes, perhaps specifying a
    # field and an order of Datasource type priority
    def refresh_description(self, overwrite_existing=False):
        if self.description == self.__class__.description.field.default:
            overwrite_existing = True
        if overwrite_existing is False:
            return (self.description, self.description)

        old_description = self.description

        # Favor Banktrack descriptions
        if banktrack_datasources := dsm.Banktrack.objects.filter(brand=self):
            if len(banktrack_datasources) > 0:
                self.description = banktrack_datasources[0].description
                self.save()
        elif bimpact_datasources := dsm.Bimpact.objects.filter(brand=self):
            if len(bimpact_datasources) > 0:
                self.description = bimpact_datasources[0].description
                self.save()

        return (old_description, self)

    def refresh_countries(self):
        """refresh countries is additive. It never removes countries from brands"""
        old_countries = self.countries
        new_countries = self.countries
        if banktrack_datasources := dsm.Banktrack.objects.filter(brand=self):
            for banktrack_datasource in banktrack_datasources:
                self.countries = old_countries + banktrack_datasource.countries
                new_countries = self.countries
        if bimpacts := dsm.Bimpact.objects.filter(brand=self):
            for bimpact in bimpacts:
                self.countries = old_countries + bimpact.countries
                new_countries = self.countries

        return old_countries, new_countries

    def refresh(self, name=True, description=True, countries=True, overwrite_existing=False):
        if name:
            self.refresh_name(overwrite_existing)
        if description:
            self.refresh_description(overwrite_existing)
        if countries:
            self.refresh_countries()

    @classmethod
    def create_brand_from_datasource(self, banks: List) -> Tuple[List, List]:
        brands_updated, brands_created = [], []

        for bank in banks:
            tag = bank.tag.replace(bank.tag_prepend_str, "")

            # brand must be saved to bank after brand creation for refresh methods to work
            brand, created = Brand.objects.get_or_create(tag=tag)
            bank.brand = brand
            bank.save()

            brand.refresh(name=True, description=True, overwrite_existing=False)
            brand.save()

            if created:
                brands_created.append(brand)
            else:
                brands_updated.append(brand)

        return (brands_created, brands_updated)

    # commented out until we finish reworking the brand-datasource association
    #
    # def return_suggested_brands_or_datasources(self):
    #     """
    #     Suggestion of data sources based on Levenshtein distance
    #     Returns a list of records of datasource subclasses
    #     """
    #     # subclass self in case it was passed as a datasource
    #     self = self.subclass()
    #     suggested_brands_or_datasources = []
    #     brands_or_datasources = Brand.objects.all()
    #     current_name = re.sub("[^0-9a-zA-Z]+", "", self.name.lower())

    #     for bods in brands_or_datasources:
    #         bods = bods.subclass()

    #         # bods of one class cannot recommend the same class
    #         if self.__class__ == bods.__class__:
    #             continue

    #         # get rid of datasources that are already associated with the brand.
    #         # In this case, self is a datasource
    #         if hasattr(self, "brand") and self.brand == bods:
    #             continue

    #         # get rids of brands that are already associated with the datasource
    #         # in this case, self is a brand
    #         if hasattr(bods, "brand") and bods.brand == self:
    #             continue

    #         bods_name = re.sub("[^0-9a-zA-Z]+", "*", bods.name.lower())
    #         if lev(bods_name, current_name) <= lev_distance:
    #             suggested_brands_or_datasources.append(bods)
    #     return suggested_brands_or_datasources
