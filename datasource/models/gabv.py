import json
from datetime import datetime, timezone

import pandas as pd

from datasource.models.datasource import Datasource, classproperty
from datasource.pycountry_utils import pycountries


class Gabv(Datasource):
    @classproperty
    def tag_prepend_str(cls):
        return cls.__name__.lower() + "_"

    @classmethod
    def load_and_create(cls):
        print("Loading Bimpact data from local copy...")
        df = pd.read_csv("./datasource/local/gabv/gabv_banks_with_text.csv")

        existing_tags = {x.tag for x in cls.objects.all()}
        banks = []
        num_created = 0
        for i, row in df.iterrows():
            try:
                num_created, existing_tags = cls._load_or_create_individual_instance(
                    existing_tags, banks, num_created, row
                )
            except Exception as e:
                print("\n\n===Bimpact failed creation or updating===\n\n")
                print(row)
                print(e)

        return banks, num_created

    @classmethod
    def _load_or_create_individual_instance(cls, existing_tags, banks, num_created, row):
        source_id = row.id
        tag = cls._generate_tag(
            og_tag=None, existing_tags=existing_tags, company_name=row.company_name, id=row.id
        )

        country = pycountries.get(row.country.lower(), None)
        defaults = {
            "date_updated": datetime.now().replace(tzinfo=timezone.utc),
            "description": row.description,
            "countries": country,
            "name": row.company_name,
            "website": row.website,
        }
        defaults = {k: v for k, v in defaults.items() if v == v and v is not None and v != ""}

        bank, created = Gabv.objects.update_or_create(source_id=source_id, defaults=defaults)

        if created:
            bank.tag = tag
            bank.save()

        banks.append(bank)
        num_created += 1 if created else 0
        return num_created, existing_tags

    @classmethod
    def _generate_tag(
        cls, og_tag=None, increment=0, existing_tags=None, company_name=None, id=None
    ):
        if company_name and id:
            og_tag = company_name.lower().strip().replace(" ", "_") + "_" + str(id)
        # memoize existing tags for faster recursion
        if not existing_tags:
            existing_tags = {x.tag for x in cls.objects.all()}

        if increment < 1:
            bt_tag = cls.tag_prepend_str + og_tag
        else:
            bt_tag = cls.tag_prepend_str + og_tag + "_" + str(increment).zfill(2)
            # bt_tag = row.tag

        if bt_tag not in existing_tags:
            return bt_tag
        else:
            return cls._generate_tag(og_tag, increment=increment + 1, existing_tags=existing_tags)
