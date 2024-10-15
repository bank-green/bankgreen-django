import json
from datetime import datetime, timezone

from django.db import models

import pandas as pd
from django_countries.fields import CountryField

from datasource.models.datasource import Datasource, classproperty
from datasource.pycountry_utils import pycountries


class Gabv(Datasource):
    @classmethod
    def load_and_create(cls):
        print("Loading Bimpact data from local copy...")
        df = pd.read_csv("./datasource/local/gabv/gabv_banks_with_text.csv")

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
        source_id = row.id

        country = pycountries.get(row.country.lower(), None)
        defaults = {
            "description": row.description,
            "countries": country,
            "name": row.company_name,
            "website": row.website,
        }
        defaults = {k: v for k, v in defaults.items() if v == v and v is not None and v != ""}

        bank, created = Gabv.objects.update_or_create(source_id=source_id, defaults=defaults)

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
