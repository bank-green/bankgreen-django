import re
from typing import List, Tuple

from django.db import models
from django.utils import timezone

import unidecode
from django_countries.fields import CountryField
from Levenshtein import distance as lev

import datasource.models as dsm
from datasource.constants import lev_distance, model_names


class Brand(models.Model):
    """
    A "Brand" is the instance shown to the end user.
    Multiple Datasources may be associated with a single brand.
    The brand's charasterics are initially determined by the data sources.
    However, they may be overwritten by the user.
    """

    name = models.CharField(
        "Name of this brand/data source",
        max_length=200,
        null=False,
        blank=False,
        default="-unnamed-",
    )
    description = models.TextField(
        "Description of this instance of this brand/data source",
        null=True,
        blank=True,
        default="-blank-",
    )
    website = models.URLField(
        "Website of this brand/data source. i.e. bankofamerica.com", null=True, blank=True
    )
    countries = CountryField(
        multiple=True, help_text="Where the brand offers retails services", blank=True
    )
    tag = models.CharField(
        max_length=100,
        null=False,
        blank=False,
        editable=True,
        unique=True,
        help_text=(
            "the tag we use or this brand/datasource record at Bank.Green. ",
            "Prepend this with the relevant datasource. i.e. banktrack_bank_of_america. "
            "for brands, prepend with nothing at all i.e. bank_of_america",
        ),
    )

    # unique identifiers
    # These are all institutional identifiers of this entity
    permid = models.CharField(max_length=15, blank=True)
    isin = models.CharField(max_length=15, blank=True)
    viafid = models.CharField(max_length=15, blank=True)
    lei = models.CharField(max_length=15, blank=True)
    googleid = models.CharField(max_length=15, blank=True)
    rssd = models.CharField(max_length=15, blank=True)
    rssd_hd = models.CharField(max_length=15, blank=True)
    cusip = models.CharField(max_length=15, blank=True)
    thrift = models.CharField(max_length=15, blank=True)
    thrift_hc = models.CharField(max_length=15, blank=True)
    aba_prim = models.CharField(max_length=15, blank=True)
    ncua = models.CharField(max_length=15, blank=True)
    fdic_cert = models.CharField(max_length=15, blank=True)
    occ = models.CharField(max_length=15, blank=True)
    ein = models.CharField(max_length=15, blank=True)
    source_link = models.URLField(
        "Link to the data source's webpage. i.e. the banktrack.org or b-impact webpage for the bank",
        editable=True,
        null=True,
        blank=True,
    )

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

    # metadata
    date_added = models.DateTimeField(default=timezone.now)
    date_updated = models.DateTimeField(
        "Time of last update", default=timezone.now, null=False, editable=True
    )
    suggested_datasource = models.TextField(blank=True, null=True, default="-blank-")
    graphql_country = models.CharField(max_length=150, blank=True, null=True)

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

        # Favor Banktrack names
        if banktrack_datasources := dsm.Banktrack.objects.filter(brand=self):
            if len(banktrack_datasources) > 0:
                new_name = banktrack_datasources[0].name
                self.name = new_name
                self.save()
                return (old_name, new_name)

        return (old_name, old_name)

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
    def suggest_tag(self):
        """
        using the bank name replace spaces with underscores.
        convert accented characters to non accented. Remove special characters.

        tag is set in the bank model
        """
        mystr = unidecode.unidecode(self.name).lower().rstrip().lstrip().replace(" ", "_")
        mystr = re.sub("[\W]", "", mystr)
        return mystr

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

    def datasource_suggestions(self):
        """Suggestion of data sources based on Levenshtein distance"""
        brand_list = []
        datasource_tags_without_model_names = []
        datasource_tags = dsm.Datasource.objects.all().values_list("tag", flat=True)
        for tag in datasource_tags:
            if tag.startswith(model_names[2]):
                tag = tag[len(model_names[2]) + 1 :]
            elif tag.startswith(model_names[0]):
                tag = tag[len(model_names[0]) + 1 :]
            elif tag.startswith(model_names[1]):
                tag = tag[len(model_names[1]) + 1 :]
            elif tag.startswith(model_names[3]):
                tag = tag[len(model_names[3]) + 1 :]
            elif tag.startswith(model_names[4]):
                tag = tag[len(model_names[4]) + 1 :]
            elif tag.startswith(model_names[5]):
                tag = tag[len(model_names[5]) + 1 :]
            elif tag.startswith(model_names[6]):
                tag = tag[len(model_names[6]) + 1 :]
            elif tag.startswith(model_names[7]):
                tag = tag[len(model_names[7]) + 1 :]
            elif tag.startswith(model_names[8]):
                tag = tag[len(model_names[8]) + 1 :]
            elif tag.startswith(model_names[9]):
                tag = tag[len(model_names[9]) + 1 :]
            datasource_tags_without_model_names.append(tag)

        for tag in datasource_tags_without_model_names:
            # get rid of the one that is equal to self
            if self.tag != tag:
                num = lev(self.tag, tag)
                if num <= lev_distance:
                    brand_list.append(tag)
        brands = ", ".join(brand_list)
        return brands

    def define_graphql_country(self):
        countries = []
        if self.countries:
            for country in self.countries:
                countries.append(country.name)
        else:
            pass
        self.graphql_country = countries

    def save(self, *args, **kwargs):
        self.suggested_datasource = self.datasource_suggestions()
        self.define_graphql_country()

        super(Brand, self).save()
