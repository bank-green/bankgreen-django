import json
from datetime import datetime, timezone
from django.db import models


from datasource.models.datasource import Datasource, classproperty


class Switchit(Datasource):
    """ """

    @classmethod
    def load_and_create(cls):
        with open("./datasource/local/switchit/providers.json") as json_file:
            data = json.load(json_file)
            # print(data['bank_providers'])

        banks = []
        num_created = 0
        for row in data["bank_providers"]:
            try:
                num_created = cls._load_or_create_individual_instance(banks, num_created, row)
            except Exception as e:
                print("\n\n===Banktrack failed creation or updating===\n\n")
                print(row)
                print(e)
        return banks, num_created

    @classmethod
    def _load_or_create_individual_instance(cls, banks, num_created, row):
        source_id = row["name"].lower().strip().replace(" ", "_")

        defaults = {"name": row["name"], "website": row["url"]}
        # filter out unnecessary defaults
        defaults = {k: v for k, v in defaults.items() if v == v and v is not None and v != ""}

        bank, created = Switchit.objects.update_or_create(source_id=source_id, defaults=defaults)

        if created:
            bank.save()

        banks.append(bank)
        num_created += 1 if created else 0
        return num_created

    website = models.URLField(
        "Website of this brand/data source. i.e. bankofamerica.com", null=True, blank=True
    )
