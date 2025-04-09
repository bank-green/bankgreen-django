import re
from typing import List, Tuple

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.query import QuerySet
from django.template.defaultfilters import truncatechars

from cities_light.models import Region, SubRegion
from django_countries.fields import CountryField
from model_utils.models import TimeStampedModel


def validate_tag(value):
    """This is the function that is used to validate the TAG"""
    if not re.match("^[a-z0-9_-]*$", str(value)):
        raise ValidationError(
            "Tag can contain only lower case alpha-numeric characters, underscores and dashes"
        )
    return value


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

    class Meta:
        ordering = ["name"]

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
        validators=[validate_tag],
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

    def __str__(self):
        return f"{self.tag}: {self.pk}"

    def __repr__(self):
        return f"<{type(self).__name__}: {self.tag}: {self.pk}>"

    def clean(self):
        super().clean()
        if Brand.objects.filter(tag=self.tag).exclude(pk=self.pk).exists():
            raise ValidationError(
                f"A brand with tag {self.tag} already exists. Please edit that brand instead."
            )

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
    def create_brand_from_usnic(self, banks: QuerySet) -> tuple[list, list, dict]:
        """
        Add new brands to database using USNIC data. Also checks for banks controlled by
        chosen Usnic entries.
        """
        existing_brands, successful_brands = [], []

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

        return existing_brands, successful_brands

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

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
