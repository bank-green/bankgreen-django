from datetime import datetime, timezone
from django.db import models


import pandas as pd

from datasource.models.datasource import Datasource, classproperty
from datasource.pycountry_utils import pycountries


class Usnic(Datasource):
    """ """

    @classmethod
    def load_and_create(cls, load_from_api=False):

        # load from api or from local disk.
        df = None
        if not load_from_api:
            print("Loading Usnic data from local copy...")
            df = pd.read_csv("./datasource/local/usnic/CSV_ATTRIBUTES_ACTIVE.CSV")
        else:
            print("Loading Usnic data from API...")
            df = pd.read_csv("./datasource/local/usnic/CSV_ATTRIBUTES_ACTIVE.CSV")

        banks = []
        num_created = 0
        for i, row in df.iterrows():
            try:
                num_created = cls._load_or_create_individual_instance(banks, num_created, row)
            except Exception as e:
                print("\n\n===Usnic failed creation or updating===\n\n")
                print(row)
                print(e)
        return banks, num_created

    @classmethod
    def _load_or_create_individual_instance(cls, banks, num_created, row):
        source_id = row.NM_SHORT.lower().strip().replace(" ", "_")

        defaults = {
            # "source_link": row.link,
            "name": row.NM_SHORT,
            "countries": pycountries.get(row.CNTRY_NM.lower(), None),
            "website": "" if row.URL == "0" else row.URL,
            "thrift": row.ID_THRIFT,
            "thrift_hc": row.ID_THRIFT_HC,
            "rssd": row[0],  # todo: fix this
            "rssd_hd": row.ID_RSSD_HD_OFF,
            "lei": row.ID_LEI,
            "cusip": row.ID_CUSIP,
            "aba_prim": row.ID_ABA_PRIM,
            "fdic_cert": row.ID_FDIC_CERT,
            "ncua": row.ID_NCUA,
            "occ": row.ID_OCC,
            "ein": row.ID_TAX,
        }
        # filter out unnecessary defaults
        defaults = {k: v for k, v in defaults.items() if v == v and v is not None and v != ""}

        bank, created = Usnic.objects.update_or_create(source_id=source_id, defaults=defaults)

        if created:
            bank.save()

        banks.append(bank)
        num_created += 1 if created else 0
        return num_created

    @classmethod
    def link_parents(cls):
        # cycle through banks again, this time adding owner relationships
        df = pd.read_csv("./datasource/local/usnic/CSV_RELATIONSHIPS.CSV")
        existing_objects = Usnic.objects.values_list("rssd", flat=True)
        for i, row in df.iterrows():
            if str(row["#ID_RSSD_PARENT"]) in list(existing_objects) and str(
                row["ID_RSSD_OFFSPRING"]
            ) in list(existing_objects):

                child = Usnic.objects.get(rssd=str(row["ID_RSSD_OFFSPRING"]))
                parent = Usnic.objects.get(rssd=str(row["#ID_RSSD_PARENT"]))

                if not child.subsidiary_of_1 or child.subsidiary_of_1 != parent:
                    # child.subsidiary_of_1 = Usnic.objects.get(rssd=str(row['#ID_RSSD_PARENT']))
                    child.subsidiary_of_1 = parent
                    child.subsidiary_of_1_pct = row["PCT_EQUITY"]
                elif not child.subsidiary_of_2 or child.subsidiary_of_2 != parent:
                    child.subsidiary_of_2 = parent
                    child.subsidiary_of_2_pct = row["PCT_EQUITY"]
                elif not child.subsidiary_of_3 or child.subsidiary_of_3 != parent:
                    child.subsidiary_of_3 = parent
                    child.subsidiary_of_3_pct = row["PCT_EQUITY"]
                elif not child.subsidiary_of_4 or child.subsidiary_of_4 != parent:
                    child.subsidiary_of_4 = parent
                    child.subsidiary_of_4_pct = row["PCT_EQUITY"]
                else:
                    pass
                child.save()

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
    lei = models.CharField(max_length=15, blank=True)
    website = models.URLField(
        "Website of this brand/data source. i.e. bankofamerica.com", null=True, blank=True
    )
