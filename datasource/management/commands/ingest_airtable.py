import os
from datetime import datetime, timezone

from django.core.management.base import BaseCommand

import pandas as pd
from airtable import Airtable
from dotenv import load_dotenv

from brand.models import Brand
from datasource.pycountry_utils import pycountries


load_dotenv()


class Command(BaseCommand):
    help = "ingest airtable data, creating new brands for non-new tags, updating existing brands"

    def add_arguments(self, parser):
        parser.add_argument(
            "--local",
            help="avoid API calls and load local data where possible. datasources for this option must be specified",
        )

    def handle(self, *args, **options):

        table_name = "staging"
        at = Airtable(base_id=os.getenv("AIRTABLE_BASE_ID"), api_key=os.getenv("AIRTABLE_API_KEY"))
        records = self._get_all_records_from_airtable_table(at, table_name)

        df = pd.DataFrame(
            [record["fields"] for record in records], index=[record["id"] for record in records]
        )

        new_brands, updated_brands = [], []
        for i, row in df.iterrows():

            # for panda reasons, name has to be accessed as a dict. Dot notation will return something else
            # test for NAN valus returned by pands. NaN != NaN
            if row["name"] != row["name"] and row.tag != row.tag:
                continue

            source_link = f"https://api.airtable.com/v0/{os.getenv('AIRTABLE_BASE_ID')}/{table_name}/{row.name}"
            brand, created = self.create_brand_from_airtable_row(row, source_link)
            if created:
                new_brands.append(brand)
            else:
                updated_brands.append(brand)

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully created {len(new_brands)} brands: {', '.join([x.tag for x in new_brands])}\n"
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully updated {len(updated_brands)} brands: {', '.join([x.tag for x in updated_brands])}\n"
            )
        )

        # rating = row['rating']

        # # text
        # unique_statement = row['Unique Statement']  # str
        # top_blurb_headline = row['top blurb headline']  # str
        # top_blurb_subheadline = row['top blurb']  # str

        # our_take = row['Our Take']  # str, should become top_blurb_subheadline.
        # if our_take != our_take:
        #     top_blurb = "Our take on " + name
        # # If our take is avialable, the top_blurb_headline should become "Our Take on [BANK NAME]"

        # headline = row['headline']  # TODO - handle blanks. make model
        # # description = row['description']  Can be ignored. Imported from bimpact

        # from_the_website = row['From the website']  # str
        # snippet_1 = row['dirty deal 1']
        # snippet_1_link = row['dirty deals link']  # todo create model
        # snippet_2 = row['dirty deal 2']

        # # recommendation metadata
        # recomended_order = row['recommended_order']  # int
        # recommend_in = [pycountries.get(country) for country in row['recommended_in']]  # country
        # top_three_ethical = row['top_three_ethical']  # bool

        # comment = row['Notes'] + row['checkings/savings offered']

        # aliases = row['aliases']  # str

        # # checking and saving confusion options
        # checking_saving = row['Checking & Savings Accounts']  # bool
        # checking_saving_details = row['Checking & Savings Accounts custom']  # str

        # _ = row['Free Checking Account Available']  # bool
        # free_checking_account_custom = row['Free Checking Account Available custom']  # str

        # interest_rates = row['Interest Rates']  # str
        # free_atm_withdrawl = row['Free ATM Withdrawl']  # bool
        # free_atm_withdrawl_details = row['Free ATM Withdrawals custom']  # str

        # online_banking = row['Mobile & Online Banking ']  # bool
        # local_branches = row['Branches Available']  # bool
        # local_branches_custom = row['Branches Available custom']  # str

        # mortgage_or_loan = row['Mortgage or Loan Options']  # bool
        # deposit_protection = row['Deposit Protection']  # str

        # credit_card = row['Credit Card']  # bool
        # free_international_card_payment = row['Free International Card Payments']  # bool
        # free_international_card_payment_details = row['Free International Card Payments custom ']  # str

        # load_from_api = False if options['local'] else False
        # if load_from_api:
        #     pass

    def create_brand_from_airtable_row(self, row, source_link):

        defaults = {
            "date_updated": datetime.now().replace(tzinfo=timezone.utc),
            "name": row["name"],
            "countries": row.country,
            "description": row.description,
            "website": row.website,
            "source_link": source_link,
        }
        # remove any NaN default values (NaN != NaN)
        defaults = {k: v for k, v in defaults.items() if v == v}

        # resolve countries
        if defaults.get("countries"):
            defaults["countries"] = [pycountries.get(country.lower()) for country in row.country]

        brand, created = Brand.objects.update_or_create(tag=row.tag, defaults=defaults)
        brand.save()

        return brand, created

    def _get_all_records_from_airtable_table(self, at: Airtable, table_name: str) -> list:
        # Airtable API limits the number of records returned to 100 per page
        # The API is unstable and the library documentation differs on their github page
        # and on the read the docs. Don't expect this to work for long
        page = at.get(table_name)
        offset = page.get("offset")
        records = page["records"]
        while offset:
            page = at.get(table_name, offset=offset)
            offset = page.get("offset")
            records += page["records"]
        return records
