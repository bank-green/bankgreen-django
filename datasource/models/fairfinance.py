import json
from datetime import datetime, timezone

import pandas as pd
from django_countries.fields import CountryField

from datasource.models.datasource import Datasource, classproperty
from datasource.pycountry_utils import pycountries


class Fairfinance(Datasource):
    """ """

    @classmethod
    def load_and_create(cls, load_from_api=False):
        # load from api or from local disk.
        df = None
        if not load_from_api:
            print("Loading Banktrack data from local copy...")
            df = pd.read_csv("./datasource/local/fairfinance/fairfinance.csv")
        else:
            print("Loading Banktrack data from API...")
            df = pd.read_csv("./datasource/local/fairfinance/fairfinance.csv")
            print(df)
            # r = requests.post(
            #     "https://www.banktrack.org/service/sections/Bankprofile/financedata",
            #     data={"pass": banktrack_password},
            # )
            # res = json.loads(r.text)
            # df = pd.DataFrame(res["bankprofiles"])
            # df.to_csv("./datasource/local/fairfinance/fairfinance.csv")

        banks = []
        num_created = 0
        for i, row in df.iterrows():
            try:
                num_created = cls._load_or_create_individual_instance(banks, num_created, row)
            except Exception as e:
                print("\n\n===Banktrack failed creation or updating===\n\n")
                print(row)
                print(e)
        return banks, num_created

    @classmethod
    def _load_or_create_individual_instance(cls, banks, num_created, row):
        source_id = row.Bank.lower().strip().replace(" ", "_")
        # from .datasource import Datasource
        # datasources = Datasource.objects.filter(source_id=source_id)
        # for da in datasources:
        #     print(da, da.name, da.source_id, '<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')

        defaults = {"name": row.Bank, "countries": pycountries.get(row.Countries.lower(), None)}
        # filter out unnecessary defaults
        defaults = {k: v for k, v in defaults.items() if v == v and v is not None and v != ""}

        bank, created = Fairfinance.objects.update_or_create(source_id=source_id, defaults=defaults)

        if created:
            bank.save()

        banks.append(bank)
        num_created += 1 if created else 0
        return num_created

    countries = CountryField(
        multiple=True, help_text="Where the bank offers retails services", blank=True
    )
