from datetime import datetime, timezone

import pandas as pd

from datasource.models.datasource import Datasource, classproperty
from datasource.pycountry_utils import pycountries
from django_countries.fields import CountryField

from django.db import models


class Bocc(Datasource):
    """
    Data from the Banking on Climate Change report published by the Rainforest Action Network
    """

    @classmethod
    def load_and_create(cls, load_from_api=False):
        # load from api or from local disk.
        df = None
        if not load_from_api:
            print("Loading BOCC data from local copy...")
            df = pd.read_csv("./datasource/local/bocc/ran_complete_2021.csv", header=0)

        banks = []
        num_created = 0
        for i, row in df.iterrows():
            try:
                num_created = cls._load_or_create_individual_instance(banks, num_created, row)
            except Exception as e:
                print("\n\n===BOCC failed creation or updating===\n\n")
                print(row)
                print(e)
        return banks, num_created

    @classmethod
    def _load_or_create_individual_instance(cls, banks, num_created, row):
        source_id = row.Bank.lower().strip().replace(" ", "_")

        defaults = {"name": row.Bank, "countries": row.Country}

        # filter out unnecessary defaults
        defaults = {k: v for k, v in defaults.items() if v == v and v is not None and v != ""}

        bank, created = Bocc.objects.update_or_create(source_id=source_id, defaults=defaults)

        if created:
            bank.save()

        banks.append(bank)
        num_created += 1 if created else 0
        return num_created

    countries = CountryField(
        multiple=True, help_text="Where the bank offers retails services", blank=True
    )

    description = models.TextField(
        "Description of this instance of this brand/data source",
        null=True,
        blank=True,
        default="-blank-",
    )
