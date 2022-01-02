import json
import requests
from datetime import datetime, timezone

from bank.models import Bank
from django.db import models

import pandas as pd

from datasource.models.datasource import Datasource
from datasource.local.banktrack.secret import PASSWORD as banktrack_password

class Banktrack(Datasource):
    update_date = models.DateTimeField(
        "Banktrack data refresh date and time", null=False, editable=False
    )
    banktrack_link = models.URLField("Link to the banktrack bank page", editable=False)
    tag = models.CharField(max_length=100, null=False, blank=False, editable=False)

    # TODO: Fix Tag Generation / storage and decide which
    # @property
    # def tag(self):
    # '''overwrites parent property. Must be lowercased and stripped to match pipeline expectations'''
    # return self.source_id.lower().rstrip().lstrip()

    @classmethod
    def load_and_create(cls, load_from_api=False):

        # load from api or from local disk.
        df = None
        if not load_from_api:
            df = pd.read_csv("./datasource/local/banktrack/bankprofiles.csv")
        else:
            r = requests.post(
                "https://www.banktrack.org/service/sections/Bankprofile/financedata",
                data={"pass": banktrack_password},
            )
            res = json.loads(r.text)
            df = pd.DataFrame(res["bankprofiles"])
            df = df.drop(columns=["general_comment"])
            df.to_csv("bankprofiles.csv")

        banks = []
        for i, row in df.iterrows():

            bank = Banktrack(
                update_date=datetime.strptime(row.updated_at, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc),
                banktrack_link=row.link,
                tag=row.tag,
                name=row.title,
                description=row.general_comment if "general_comment" in row.values else "",
                website=row.website
                # TODO: Parse Countries for adding. Maybe override __init__? country=row.country,
            )
            bank.save()
            banks.append(bank)

        return banks
