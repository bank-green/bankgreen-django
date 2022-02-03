import re
from typing import List, Tuple

import datasource.models as dsm
import unidecode
from django.db import models
from django.utils import timezone
from numpy import DataSource


class Brand(models.Model):
    """
    A "Brand" is the instance shown to the end user.
    Multiple Datasources may be associated with a single brand.
    The brand's charasterics are initially determined by the data sources.
    However, they may be overwritten by the user.
    """

    name = models.CharField(
        "Name of this brand/data source", max_length=200, null=False, blank=False, default="-unnamed-"
    )
    description = models.TextField("Description of this instance of this brand/data source", null=True, blank=True)
    website = models.URLField("Website of this brand/data source", null=True, blank=True)
    countries = models.CharField(max_length=200, blank=True)  # TODO: Make this a list
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

    # display snippets
    snippet_1 = models.TextField(
        "Custom fact about the brand.", help_text="Used to fill in templates", blank=True, default=''
    )
    snippet_2 = models.TextField(
        "Custom fact about the brand.", help_text="Used to fill in templates", blank=True, default=''
    )
    snippet_3 = models.TextField(
        "Custom fact about the brand.", help_text="Used to fill in templates", blank=True, default=''
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

    # subsidiary information. Subsidiaries should be listed in descending order of ownership
    # i.e. a DataSource A wholly owned by DataSource B would have subsidiary_of_1 set to B, and
    # subsidiary_of_1_pct set to 100
    subsidiary_of_1 = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, related_name="subsidiary_of_1_data_source", blank=True
    )
    subsidiary_of_1_pct = models.IntegerField("percentage owned by subsidiary 1", default=0)
    subsidiary_of_2 = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, related_name="subsidiary_of_2_data_source", blank=True
    )
    subsidiary_of_2_pct = models.IntegerField("percentage owned by subsidiary 2", default=0)
    subsidiary_of_3 = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, related_name="subsidiary_of_3_data_source", blank=True
    )
    subsidiary_of_3_pct = models.IntegerField("percentage owned by subsidiary 3", default=0)
    subsidiary_of_4 = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, related_name="subsidiary_of_4_data_source", blank=True
    )
    subsidiary_of_4_pct = models.IntegerField("percentage owned by subsidiary 4", default=0)

    # metadata
    date_added = models.DateTimeField(default=timezone.now)
    date_updated = models.DateTimeField("Time of last update", default=timezone.now, null=False, editable=True)

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
                return (old_description, self.description)

        return (old_description, old_description)

    def refresh(self, name=True, description=True, overwrite_existing=False):
        if name:
            self.refresh_name(overwrite_existing)
        if description:
            self.refresh_description(overwrite_existing)

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
    def create_brand_from_datasource(self, banks: List[DataSource]) -> Tuple[List, List]:
        brands_updated, brands_created = [], []

        for bank in banks:
            tag = bank.tag.replace(bank.tag_prepend_str, '')

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
