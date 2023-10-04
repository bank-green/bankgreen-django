import json
from datetime import datetime, timezone
from pathlib import Path
from re import I

from django.conf import settings
from django.db import models
from django_countries.fields import CountryField


import pandas as pd
import requests

# from datasource.local.banktrack.secret import PASSWORD as banktrack_password
from datasource.models.datasource import Datasource, classproperty
from datasource.pycountry_utils import pycountries


class Banktrack(Datasource):
    @classproperty
    def tag_prepend_str(cls):
        return cls.__name__.lower() + "_"

    @classmethod
    def load_and_create(cls, load_from_api=False):

        # load from api or from local disk.
        df = None
        if not load_from_api:
            print("Loading Banktrack data from local copy...")
            df = pd.read_csv("./datasource/local/banktrack/banktrack.csv")
        else:
            print("Loading Banktrack data from api...")
            df = pd.read_csv("./datasource/local/banktrack/banktrack.csv")
            # r = requests.post(
            #     "https://www.banktrack.org/service/sections/Bankprofile/financedata",
            #     data={"pass": settings.PASSWORD},
            # )
            # res = json.loads(r.text)
            # df = pd.DataFrame(res["bankprofiles"])
            # df.to_csv("./datasource/local/banktrack/banktrack.csv")

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
        tag = cls._generate_tag(bt_tag=row.tag, existing_tags=existing_tags)
        source_id = row.tag

        defaults = {
            "source_link": row.link,
            "name": row.title,
            "countries": pycountries.get(row.country.lower(), None),
            "description": row.general_comment,
            "website": row.website,
        }
        # filter out unnecessary defaults
        defaults = {k: v for k, v in defaults.items() if v == v and v is not None and v != ""}

        bank, created = Banktrack.objects.update_or_create(source_id=source_id, defaults=defaults)

        if created:
            bank.tag = tag
            bank.save()

        banks.append(bank)
        num_created += 1 if created else 0
        existing_tags.add(tag)
        return num_created, existing_tags

    @classmethod
    def _generate_tag(cls, bt_tag, increment=0, existing_tags=None):
        og_tag = bt_tag

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

    countries = CountryField(
        multiple=True, help_text="Where the bank offers retails services", blank=True
    )

    tag = models.CharField(
        max_length=100,
        null=False,
        blank=False,
        editable=True,
        unique=True,
        help_text=("Banktrack's own tag, has format bank_of_america",),
    )

    website = models.URLField(
        "Website of this entry. i.e. bankofamerica.com", null=True, blank=True
    )

    description = models.TextField(
        "Description of this entry", null=True, blank=True, default="-blank-"
    )
