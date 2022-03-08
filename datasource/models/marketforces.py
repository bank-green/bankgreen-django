import json
from datetime import datetime, timezone

from django.db import models

import pandas as pd
import requests

from datasource.models.datasource import Datasource


class Marketforces(Datasource):
    """ """

    @classmethod
    def load_and_create(cls, load_from_api=False):

        # load from api or from local disk.
        df = None
        if not load_from_api:
            print("Loading Banktrack data from local copy...")
            df = pd.read_csv("./datasource/local/marketforces/marketforces.csv")
        else:
            print("Loading Banktrack data from API...")
            df = pd.read_csv("./datasource/local/marketforces/marketforces.csv")
            print(df)
            # r = requests.post(
            #     "https://www.banktrack.org/service/sections/Bankprofile/financedata",
            #     data={"pass": banktrack_password},
            # )
            # res = json.loads(r.text)
            # df = pd.DataFrame(res["bankprofiles"])
            # df.to_csv("./datasource/local/marketforces/marketforces.csv")

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
        tag = cls._generate_tag(og_tag=None, existing_tags=existing_tags, bank=row.Name)
        source_id = row.Name.lower().strip().replace(" ", "_")

        defaults = {"date_updated": datetime.now(), "name": row.Name}
        # filter out unnecessary defaults
        defaults = {k: v for k, v in defaults.items() if v == v and v is not None and v != ""}

        bank, created = Marketforces.objects.update_or_create(
            source_id=source_id, defaults=defaults
        )

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
