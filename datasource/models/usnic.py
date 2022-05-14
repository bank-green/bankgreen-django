from datetime import datetime, timezone

import pandas as pd

from datasource.models.datasource import Datasource, classproperty
from datasource.pycountry_utils import pycountries


class Usnic(Datasource):
    """ """

    @classproperty
    def tag_prepend_str(cls):
        return cls.__name__.lower() + "_"

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

        existing_tags = {x.tag for x in cls.objects.all()}
        banks = []
        num_created = 0
        for i, row in df.iterrows():
            try:
                num_created, existing_tags = cls._load_or_create_individual_instance(
                    existing_tags, banks, num_created, row
                )
            except Exception as e:
                print("\n\n===Usnic failed creation or updating===\n\n")
                print(row)
                print(e)
        return banks, num_created

    @classmethod
    def _load_or_create_individual_instance(cls, existing_tags, banks, num_created, row):
        # tag = cls._generate_tag(bt_tag=row.NM_SHORT, existing_tags=existing_tags)
        tag = cls._generate_tag(og_tag=None, existing_tags=existing_tags, bank=row.NM_LGL)

        source_id = row.NM_SHORT.lower().strip().replace(" ", "_")

        defaults = {
            "date_updated": datetime.now().replace(tzinfo=timezone.utc),
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
            bank.tag = tag
            bank.save()

        banks.append(bank)
        num_created += 1 if created else 0
        existing_tags.add(tag)
        return num_created, existing_tags

    @classmethod
    def _generate_tag(cls, og_tag=None, increment=0, existing_tags=None, bank=None):

        if bank:
            og_tag = bank.lower().strip().replace(" ", "_")

        # memoize existing tags for faster recursion
        if not existing_tags:
            existing_tags = {x.tag for x in cls.objects.all()}

        if increment < 1:
            bt_tag = cls.tag_prepend_str + og_tag
        else:
            bt_tag = cls.tag_prepend_str + og_tag + "_" + str(increment).zfill(2)

        if bt_tag not in existing_tags:
            return bt_tag
        else:
            return cls._generate_tag(og_tag, increment=increment + 1, existing_tags=existing_tags)

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
