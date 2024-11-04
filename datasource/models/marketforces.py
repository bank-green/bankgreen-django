import json
from datetime import datetime, timezone

import pandas as pd

from datasource.models.datasource import Datasource, classproperty


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
        source_id = row.Name.lower().strip().replace(" ", "_")

        defaults = {"name": row.Name}
        # filter out unnecessary defaults
        defaults = {k: v for k, v in defaults.items() if v == v and v is not None and v != ""}

        bank, created = Marketforces.objects.update_or_create(
            source_id=source_id, defaults=defaults
        )

        if created:
            bank.save()

        banks.append(bank)
        num_created += 1 if created else 0
        return num_created
