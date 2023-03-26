import re
from typing import List, Tuple

from django.db import models
from django.db.models.query import QuerySet
from django.template.defaultfilters import truncatechars

from cities_light.models import Region, SubRegion
from django_countries.fields import CountryField
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

    # unique identifiers
    # These are all institutional identifiers of this entity
    permid = models.TextField(default="", blank=True)
    isin = models.TextField(default="", blank=True)
    viafid = models.TextField(default="", blank=True)
    lei = models.TextField(default="", blank=True)
    googleid = models.TextField(default="", blank=True)
    rssd = models.TextField(default="", blank=True)
    rssd_hd = models.TextField(default="", blank=True)
    cusip = models.TextField(default="", blank=True)
    thrift = models.TextField(default="", blank=True)
    thrift_hc = models.TextField(default="", blank=True)
    aba_prim = models.TextField(default="", blank=True)
    ncua = models.TextField(default="", blank=True)
    fdic_cert = models.TextField(default="", blank=True)
    occ = models.TextField(default="", blank=True)
    ein = models.TextField(default="", blank=True)

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
        return f"{self.tag}: {self.pk}"

    def __repr__(self):
        return f"<{type(self).__name__}: {self.tag}: {self.pk}>"

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
    def create_brand_from_banktrack(self, banks: List) -> Tuple[List, List]:
        """
        Add new brands to database using banktrack data.
        """
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

    @classmethod
    def create_brand_from_usnic(self, banks: QuerySet) -> tuple[list, list, list]:
        """
        Add new brands to database using USNIC data. Also checks for banks controlled by
        chosen Usnic entries.
        """
        existing_brands, successful_brands, child_brands = [], [], []

        for bank in banks:
            # Don't create new brand if it already exists
            if bank["source_id"] in [x.tag for x in Brand.objects.all()]:
                existing_brands.append(bank["name"])
            # Otherwise create new brand with USNIC data
            else:
                brand = Brand(
                    tag=bank["source_id"],
                    id=bank["id"],
                    name=bank["name"],
                    countries=bank["country"],
                    lei=bank["lei"],
                    ein=bank["ein"],
                    rssd=bank["rssd"],
                    cusip=bank["cusip"],
                    thrift=bank["thrift"],
                    thrift_hc=bank["thrift_hc"],
                    aba_prim=bank["aba_prim"],
                    ncua=bank["ncua"],
                    fdic_cert=bank["fdic_cert"],
                    occ=bank["occ"],
                )
                brand.save()

                # Add regions, if any
                if "regions" in list(bank.keys()):
                    for region in bank["regions"]:
                        brand.regions.add(region)

                # Add subregions, if any
                if "subregions" in list(bank.keys()):
                    for subregion in bank["subregions"]:
                        brand.regions.add(subregion)

                successful_brands.append(bank["name"])

            # Check for 'child' banks controlled by chosen Usnic entries
            for item in Usnic.objects.all().values():
                if len(item['control']) > 0:
                    for parent in list(item['control'].values()):
                        if not isinstance(parent, str):
                            if parent['parent_rssd'] == int(bank['rssd']):
                                child_brands.append(item['control'])

        return existing_brands, successful_brands, child_brands

    @classmethod
    def _non_replacing_insert(cls, mydict: dict, key, value) -> dict:
        if (
            value
            and value != ""
            and value != "0"
            and key
            and key != ""
            and key != "0"
            and not mydict.get(key)
        ):
            mydict[key] = value
        return mydict

    @classmethod
    def _aliases_into_spelling_dict(cls, brand, spelling_dict):
        if brand.aliases:
            aliases = [x.strip() for x in brand.aliases.split(",")]
            for alias in aliases:
                # aliases should not overwrite others
                spelling_dict[alias] = spelling_dict.get(alias, brand.pk)
        return spelling_dict

    @classmethod
    def _abbreviations_into_spelling_dict(cls, brand, spelling_dict):
        abbrev = re.sub("[^A-Z]", "", brand.name).lower()
        cls._non_replacing_insert(spelling_dict, abbrev, brand.pk)
        abbrev = re.sub("[^A-Z0-9]", "", brand.name).lower()
        spelling_dict[abbrev] = spelling_dict.get(abbrev, brand.pk)
        return spelling_dict

    @classmethod
    def website_into_spelling_dict(cls, brand, spelling_dict):
        if brand.website:
            web_sans_prefix = re.sub(
                "http(s)?(:)?(\/\/)?|(\/\/)?(www\.)?", "", brand.website
            ).strip("/")
            domain_matches = re.match(r"^(?:\/\/|[^\/]+)*", web_sans_prefix).group(0)

            spelling_dict[web_sans_prefix] = spelling_dict.get(web_sans_prefix, brand.pk)
            if domain_matches and domain_matches != "":
                spelling_dict[domain_matches] = spelling_dict.get(domain_matches, brand.pk)
        return spelling_dict

    @classmethod
    def create_spelling_dictionary(cls):
        brands = Brand.objects.all()
        spelling_dict = {}
        for brand in brands:
            spelling_dict[brand.name.lower()] = brand.pk

            # abbreviations with and without numbers. Should not overwrite existing keys
            spelling_dict = cls._abbreviations_into_spelling_dict(brand, spelling_dict)
            spelling_dict = cls._aliases_into_spelling_dict(brand, spelling_dict)
            spelling_dict = cls.website_into_spelling_dict(brand, spelling_dict)

            for identifier in (
                brand.lei,
                brand.permid,
                brand.viafid,
                brand.googleid,
                brand.rssd,
                brand.rssd_hd,
                brand.cusip,
                brand.thrift,
                brand.thrift_hc,
                brand.aba_prim,
                brand.ncua,
                brand.fdic_cert,
                brand.occ,
                brand.ein,
            ):
                spelling_dict = cls._non_replacing_insert(spelling_dict, identifier, brand.pk)

        spelling_dict = {
            k: v
            for k, v in spelling_dict.items()
            if k and v and k != "" and k != "0" and v != "" and v != "0"
        }

        return spelling_dict

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
