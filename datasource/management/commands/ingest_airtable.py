from datetime import datetime, timezone

from django.conf import settings
from django.core.management.base import BaseCommand

import pandas as pd
from airtable import Airtable
from dotenv import load_dotenv

from brand.models import Brand, Commentary, RatingChoice
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
        df = self.return_local_or_remote_df(options, table_name)
        new_brands, updated_brands = [], []
        new_commentary, updated_comentary = [], []

        for i, row in df.iterrows():
            # for panda reasons, name has to be accessed as a dict. Dot notation will return something else
            # test for NAN valus returned by pands. NaN != NaN
            if row["name"] != row["name"] and row.tag != row.tag:
                continue

            # create brands
            brand, brand_created = self.create_brand_from_airtable_row(row)
            if brand_created:
                new_brands.append(brand)
            else:
                updated_brands.append(brand)

            # create and associate commentary
            commentary, commentary_created = self.create_commentary_from_airtable_row(row, brand)
            if commentary_created:
                new_commentary.append(commentary)
            else:
                updated_comentary.append(commentary)

        self.output_creation_or_update(new_brands, updated_brands, Brand)
        self.output_creation_or_update(new_commentary, updated_comentary, Commentary)

    def return_local_or_remote_df(self, options, table_name):
        load_from_api = True
        load_from_api = False if options["local"] and "all" in options["local"] else True
        if options["local"] and "airtable" in options["local"]:
            load_from_api = False

        df = None
        if load_from_api:
            self.stdout.write(self.style.NOTICE(f"Loading airtable data from API...\n"))
            at = Airtable(base_id=settings.AIRTABLE_BASE_ID, api_key=settings.AIRTABLE_API_KEY)
            records = self._get_all_records_from_airtable_table(at, table_name)
            df = pd.DataFrame(
                [record["fields"] for record in records], index=[record["id"] for record in records]
            )
            df.to_csv("./datasource/local/airtable/airtable.csv")
        else:
            self.stdout.write(self.style.NOTICE(f"Loading airtable data from local...\n"))
            df = pd.read_csv("./datasource/local/airtable/airtable.csv")
        return df

    def create_commentary_from_airtable_row(self, row, brand):

        rating = row["rating"]
        if rating != rating:
            rating = "unknown"
        else:
            rating = rating.lower().strip()

        if "good" in rating or "great" in rating:
            rating = RatingChoice.GREAT
        elif "ok" in rating or "okay" in rating:
            rating = RatingChoice.OK
        elif "bad" in rating:
            rating = RatingChoice.BAD
        elif "worst" in rating:
            rating = RatingChoice.WORST
        else:
            rating = RatingChoice.UNKNOWN

        defaults = {
            "aliases": row.aliases,
            "display_on_website": True,
            "comment": row.Notes,
            "rating": rating,
            "unique_statement": row["Unique Statement"],
            "headline": row.headline,
            "top_blurb_headline": row["top blurb headline"],
            "top_blurb_subheadline": row["top blurb"],
            "snippet_1": row["dirty deal 1"],
            "snippet_1_link": row["dirty deals link"],
            "snippet_2": row["dirty deal 2"],
            "top_three_ethical": row["Top 3 Ethical"],  # bool
            "recommended_order": row["recommended_order"],  # int
            "recommended_in": row["recommended_in"],  # country
            "from_the_website": row["From the website"],  # str
            "checking_saving": row["Checking & Savings Accounts"],  # bool
            "checking_saving_details": row["Checking & Savings Accounts custom"],
            "free_checking": row["Free Checking Account Available"],  # bool
            "free_checking_details": row["Free Checking Account Available custom"],
            "interest_rates": row["Interest Rates"],  # str
            "free_atm_withdrawl": row["Free ATM Withdrawals"],  # bool
            "free_atm_withdrawl_details": row["Free ATM Withdrawals custom"],  # str
            "online_banking": row["Mobile & Online Banking"],  # bool
            "local_branches": row["Branches Available"],  # bool
            "local_branches_details": row["Branches Available custom"],  # str
            "mortgage_or_loan": row["Mortgage or Loan Options"],  # bool
            "deposit_protection": row["Deposit Protection"],  # str
            "credit_cards": row["Credit Card"],  # bool
            "free_international_card_payment": row["Free International Card Payments"],  # bool
            "free_international_card_payment_details": row[
                "Free International Card Payments custom"
            ],  # str
        }
        # remove any NaN default values (NaN != NaN)
        defaults = {k: v for k, v in defaults.items() if v == v}

        # lowercase aliases
        if aliases := defaults.get("aliases"):
            defaults["aliases"] = aliases.lower()

        # resolve countries
        if defaults.get("recommended_in"):
            defaults["recommended_in"] = [
                pycountries.get(country.lower()) for country in row.country
            ]

        commentary, created = Commentary.objects.update_or_create(brand=brand, defaults=defaults)
        commentary.save()

        return commentary, created

    def output_creation_or_update(self, new_brands, updated_brands, model_type):

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully created {len(new_brands)} {model_type} from Airtable: {', '.join([str(x) for x in new_brands])}\n"
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully updated {len(updated_brands)} {model_type} from Airtable: {', '.join([str(x) for x in updated_brands])}\n"
            )
        )

    def create_brand_from_airtable_row(self, row):

        defaults = {
            "date_updated": datetime.now().replace(tzinfo=timezone.utc),
            "name": row["name"],
            "countries": row.country,
            "description": row.description,
            "website": row.website,
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
