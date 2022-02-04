import json
import logging.config
from datetime import datetime, timezone

import pandas as pd
import requests

from datasource.local.bimpact.secret import TOKEN, USERNAME
from datasource.models.datasource import Datasource
from datasource.pycountry_utils import pycountries


class Bimpact(Datasource):
    """ """

    @classmethod
    def load_and_create(cls, load_from_api=False):
        df = None

        # hardcoded as false at the present time because of lack of
        # access API credentials. Awaiting approval
        load_from_api = False  # TODO: remove this line

        if not load_from_api:
            print("Loading Bimpact data from local copy...")
            df = pd.read_csv("./datasource/local/bimpact/bimpact.csv")
        else:
            print("Loading Bimpact data from API...")

            with open('./datasource/local/bimpact/bimpact.sql') as f:
                query = f.read()

            uri = f"https://api.data.world/v0/sql/${USERNAME}/api-sandbox"
            headers = {"Authorization": f"Bearer ${TOKEN}", "Accept": "text/csv"}
            data = {'query': query}
            r = requests.post('https://api.data.world/v0/sql/USERNAME/api-sandbox', headers=headers, data=data)

            res = json.loads(r.text)
            # df = pd.DataFrame(res["bankprofiles"])
            df.to_csv("./datasource/local/bimpact/bimpact.csv")

        existing_tags = {x.tag for x in cls.objects.all()}
        banks = []
        num_created = 0
        for i, row in df.iterrows():
            try:
                num_created, existing_tags = cls._load_or_create_individual_instance(
                    existing_tags, banks, num_created, row
                )
            except Exception as e:
                print('\n\n===Bimpact failed creation or updating===\n\n')
                print(row)
                print(e)

        return banks, num_created

    @classmethod
    def _load_or_create_individual_instance(cls, existing_tags, banks, num_created, row):
        source_id = row.company_id
        tag = cls._generate_tag(
            og_tag=None, existing_tags=existing_tags, company_name=row.company_name, company_id=row.company_id
        )

        country = pycountries.get(row.country.lower(), None)

        bank, created = Bimpact.objects.update_or_create(
            source_id=source_id,
            defaults={
                'date_updated': datetime.strptime(row.date_certified, "%Y-%m-%d").replace(tzinfo=timezone.utc),
                'source_link': row.b_corp_profile,
                'description': row.description,
                'countries': country,
                'name': row.company_name,
                'website': row.website,
            },
        )

        if created:
            bank.tag = tag
            bank.save()

        banks.append(bank)
        num_created += 1 if created else 0
        return num_created, existing_tags

    @classmethod
    def _generate_tag(cls, og_tag=None, increment=0, existing_tags=None, company_name=None, company_id=None):

        if company_name and company_id:
            og_tag = company_name.lower().strip().replace(" ", "_") + "_" + str(company_id)

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
