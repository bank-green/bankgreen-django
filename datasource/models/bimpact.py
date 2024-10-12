import json
from datetime import datetime, timezone

from django.conf import settings
from django.db import models

import pandas as pd
import requests
from django_countries.fields import CountryField

from datasource.models.datasource import Datasource, classproperty
from datasource.pycountry_utils import pycountries


class Bimpact(Datasource):
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

            with open("./datasource/local/bimpact/bimpact.sql") as f:
                query = f.read()

            uri = f"https://api.data.world/v0/sql/${settings.USERNAME}/api-sandbox"
            headers = {"Authorization": f"Bearer ${settings.TOKEN}", "Accept": "text/csv"}
            data = {"query": query}
            r = requests.post(
                "https://api.data.world/v0/sql/USERNAME/api-sandbox", headers=headers, data=data
            )

            res = json.loads(r.text)
            df.to_csv("./datasource/local/bimpact/bimpact.csv")

        banks = []
        num_created = 0
        for i, row in df.iterrows():
            try:
                num_created = cls._load_or_create_individual_instance(banks, num_created, row)
            except Exception as e:
                print("\n\n===Bimpact failed creation or updating===\n\n")
                print(row)
                print(e)

        return banks, num_created

    @classmethod
    def _load_or_create_individual_instance(cls, banks, num_created, row):
        source_id = row.company_id

        country = pycountries.get(row.country.lower(), None)

        defaults = {
            "source_link": row.b_corp_profile,
            "description": row.description,
            "countries": country,
            "name": row.company_name,
            "website": row.website,
        }
        defaults = {k: v for k, v in defaults.items() if v == v and v is not None and v != ""}

        bank, created = Bimpact.objects.update_or_create(source_id=source_id, defaults=defaults)

        if created:
            bank.save()

        banks.append(bank)
        num_created += 1 if created else 0
        return num_created

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
