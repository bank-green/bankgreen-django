import json
from datetime import datetime, timezone

from django.db import models

import requests

from datasource.models.datasource import Datasource


class Usnic(Datasource):
    """ """

    @classmethod
    def load_and_create(cls, load_from_api=False):

        # load from api or from local disk.
        df = None
        if not load_from_api:
            print("Loading Usnic data from local copy...")
            df = pd.read_csv("./datasource/local/usnic/CSV_ATTRIBUTES_ACTIVE.csv")
        else:
            print("Loading Usnic data from API...")
            df = pd.read_csv("./datasource/local/usnic/CSV_ATTRIBUTES_ACTIVE.csv")

        existing_tags = {x.tag for x in cls.objects.all()}
        banks = []
        num_created = 0
        for i, row in df.iterrows():
            try:
                num_created, existing_tags = cls._load_or_create_individual_instance(
                    existing_tags, banks, num_created, row
                )
            except Exception as e:
                print("\n\n===Banktrack failed creation or updating===\n\n")
                print(row)
                print(e)
        return banks, num_created

    @classmethod
    def _load_or_create_individual_instance(cls, existing_tags, banks, num_created, row):
        tag = cls._generate_tag(bt_tag=row.tag, existing_tags=existing_tags)
        source_id = row.tag

        defaults = {
            "date_updated": datetime.strptime(row.updated_at, "%Y-%m-%d %H:%M:%S").replace(
                tzinfo=timezone.utc
            ),
            "source_link": row.link,
            "name": row.NM_SHORT,
            "countries": pycountries.get(row.country.lower(), None),
            "website": row.URL,
            "thrift": row.ID_THRIFT,
            "thrift_hc": row.ID_THRIFT_HC,
            # "rssd": row.#ID_RSSD,  #todo: fix this
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

        bank, created = Banktrack.objects.update_or_create(source_id=source_id, defaults=defaults)

        if created:
            bank.tag = tag
            bank.save()

        banks.append(bank)
        num_created += 1 if created else 0
        existing_tags.add(tag)
        return num_created, existing_tags

    @classmethod
    def _generate_tag(cls, bt_tag, increment=0, existing_tags=None):
        og_tag = bt_tag

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
