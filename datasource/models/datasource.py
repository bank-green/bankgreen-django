import datetime
import json
import re

import pandas as pd
import requests
import unidecode
from bank.models import Bank
from django.db import models

# from .secret import PASSWORD as password

# from datasource_models import Banktrack


class Datasource(models.Model):
    """
    Datasource is the parent of various individual datasources.
    A "Datasource" is never instantiated directly - only as an instance of data from a data provider.
    Sometimes programs make use of the Datasource model, while other times they access the child instance directly
    """

    # human readable characteristics
    name = models.CharField(
        "Name of this data source", max_length=200, null=False, blank=False, default="-unnamed-"
    )
    description = models.TextField(
        "Description of this instance of a data source", null=True, blank=True
    )
    website = models.URLField("Website of this data source", null=True, blank=True)
    # TODO: Make this a list
    countries = models.CharField(max_length=200)

    # Relationships to Bank
    # TODO: Read Docs on on_delete and adjust models accordingly
    bank = models.ForeignKey(Bank, null=True, blank=True, on_delete=models.SET_NULL)

    # unique identifiers
    # These are all institutional identifiers of this entity
    permid = models.CharField(max_length=15)
    isin = models.CharField(max_length=15)
    viafid = models.CharField(max_length=15)
    lei = models.CharField(max_length=15)
    googleid = models.CharField(max_length=15)
    wikiid = models.CharField(max_length=15)
    rssd = models.CharField(max_length=15)
    rssd_hd = models.CharField(max_length=15)
    cusip = models.CharField(max_length=15)
    thrift = models.CharField(max_length=15)
    thrift_hc = models.CharField(max_length=15)
    aba_prim = models.CharField(max_length=15)
    ncua = models.CharField(max_length=15)
    fdic_cert = models.CharField(max_length=15)
    occ = models.CharField(max_length=15)
    ein = models.CharField(max_length=15)

    # subsidiary information. Subsidiaries should be listed in descending order of ownership
    # i.e. a DataSource A wholly owned by DataSource B would have subsidiary_of_1 set to B, and
    # subsidiary_of_1_pct set to 100
    subsidiary_of_1 = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, related_name="subsidiary_of_1_data_source"
    )
    subsidiary_of_1_pct = models.IntegerField("percentage owned by subsidiary 1", default=0)
    subsidiary_of_2 = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, related_name="subsidiary_of_2_data_source"
    )
    subsidiary_of_2_pct = models.IntegerField("percentage owned by subsidiary 2", default=0)
    subsidiary_of_3 = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, related_name="subsidiary_of_3_data_source"
    )
    subsidiary_of_3_pct = models.IntegerField("percentage owned by subsidiary 3", default=0)
    subsidiary_of_4 = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, related_name="subsidiary_of_4_data_source"
    )
    subsidiary_of_4_pct = models.IntegerField("percentage owned by subsidiary 4", default=0)

    # metadata
    date_added = models.DateTimeField(default=datetime.datetime.now)

    def suggest_tag(self):
        """
        using the bank name replace spaces with underscores.
        convert accented characters to non accented. Remove special characters.

        tag is set in the bank model
        """
        mystr = unidecode.unidecode(self.name).lower().rstrip().lstrip().replace(' ', '_')
        mystr = re.sub('[\W]', '', mystr)
        return mystr


# class Banktrack(Datasource):
#     update_date = models.DateTimeField(
#         "Banktrack data refresh date and time", null=False, editable=False
#     )
#     banktrack_link = models.URLField("Link to the banktrack bank page", editable=False)
#     tag = models.CharField(max_length=100, null=False, blank=False, editable=False)

#     # TODO: Fix Tag Generation / storage and decide which
#     # @property
#     # def tag(self):
#     # '''overwrites parent property. Must be lowercased and stripped to match pipeline expectations'''
#     # return self.source_id.lower().rstrip().lstrip()

#     @classmethod
#     def load_and_create(cls, load_from_api=False):

#         # load from api or from local disk.
#         # this is here because we don't have permission to publish one column of the data in this table
#         # and definitely don't have permission for opening up BankTrack's api.
#         df = None
#         if not load_from_api:
#             df = pd.read_csv("./datasource/local/banktrack/bankprofiles.csv")
#         else:
#             r = requests.post(
#                 "https://www.banktrack.org/service/sections/Bankprofile/financedata",
#                 data={"pass": password},
#             )
#             res = json.loads(r.text)
#             df = pd.DataFrame(res["bankprofiles"])
#             df = df.drop(columns=["general_comment"])
#             df.to_csv("bankprofiles.csv")

#         for i, row in df.iterrows():
#             bank = Banktrack(
#                 update_date=row.updated_at,  # TODO: Make these timezone aware
#                 banktrack_link=row.link,
#                 tag=row.tag,
#                 name=row.title,
#                 description=row.general_comment if "general_comment" in row.values else "",
#                 website=row.website
#                 # TODO: Parse Countries for adding. Maybe override __init__? country=row.country,
#             )
#             bank.save()
