import traceback
from qwikidata.sparql import return_sparql_query_results
from django.db import models
from django_countries.fields import CountryField


import pandas as pd
import np

from datasource.models.datasource import Datasource, classproperty
from datasource.local.wikidata.pycountry_util import find_country


class Wikidata(Datasource):
    """
    Wikidata has a community sourced dataset of banks, various unique identifiers, and their countries of operation.
    Data is collected via the Wikidata.org api. The api sometimes times out when hit too often, so be sure not to
    do that.
    The most important things we collect from wikidata are subsidiary information and unique bank ids including
    - Legal Entity Identifier,
    - Permanent ID
    These ID's are used for de-duplication of banks.
    """

    @classmethod
    def load_and_create(cls, load_from_api=False):
        # load from api or from local disk.
        df = None
        if not load_from_api:
            print("Loading Wikidata data from local copy...")
            df = pd.read_csv("./datasource/local/wikidata/wikidata.csv")
        else:
            print("Loading Wikidata data from api...")
            with open("./datasource/local/wikidata/query.sparql") as query_file:
                myquery = query_file.read()
            res = return_sparql_query_results(myquery)
            df = pd.json_normalize(res["results"]["bindings"])
            df.to_csv("./datasource/local/wikidata/wikidata.csv")

        return cls._create(df)

    @classmethod
    def _create(cls, df):
        # remove all parent/subsidiary_of relationships that are not banks.
        bank_values = set(df["bank.value"])

        def only_allowed(val):
            if val in bank_values:
                return val
            return np.nan

        df["parent.value"] = df["parent.value"].apply(only_allowed)

        # cycle through banks and add them, temporarily ignoring parent relationships
        banks = []
        num_created = 0
        bank_values = set(df["bank.value"])
        for bank_value in bank_values:
            bank_df = df[df["bank.value"] == bank_value]

            try:
                num_created = cls._maybe_create_individual_instance(banks, num_created, bank_df)
            except Exception as e:
                print("\n\n===Wikidata failed creation or updating===\n\n")
                print(bank_value)
                print(bank_df)
                print(e)
                traceback.print_exc()

        return banks, num_created

    @classmethod
    def _random_element_or_none(cls, df):
        """given a dataframe, discard nan.
        Return a random item of the dataframe or None if it is is empty"""
        aset = {x for x in set(df) if x == x}

        res = None
        if len(aset) > 0:
            res = list(aset)[0]
        return res

    @classmethod
    def _maybe_create_individual_instance(cls, banks, num_created, df):
        """
        Parse a dataframe looking for the bank uri. Extract values from it and instantiate a bank
        if the bank is probably a modern one.
        """
        # get a single name for the bank
        name = cls._random_element_or_none(df["bankLabel.value"])
        if name is None:
            print(f"skipping {link} because it has no name")
            return num_created

        # get the languages of the name
        language = cls._random_element_or_none(df["bankLabel.xml:lang"])
        website = cls._random_element_or_none(df["website.value"])

        countries = set(df["countryLabel.value"])
        countries = {x for x in countries if x == x}

        # get the identifiers
        permid = cls._random_element_or_none(df["permid.value"])
        isin = cls._random_element_or_none(df["isin.value"])
        viafid = cls._random_element_or_none(df["viafid.value"])
        lei = cls._random_element_or_none(df["lei.value"])
        # unclear why, but qwikidata falls over when using ?googleid as a parm. use gid instead.
        googleid = cls._random_element_or_none(df["gid.value"])

        # get random description
        description = cls._random_element_or_none(df["bankDescription.value"])

        link = cls._random_element_or_none(df["bank.value"])

        # used only for excluding banks that have been closed
        closing_year = df["deathyear.value"]
        closing_year = {x for x in closing_year if x == x}

        # is the bank's country current or historical?
        # if it's a historical country, don't add to the dataset
        country_tuples = [find_country(x) for x in countries]

        modern_country = True
        for mytup in country_tuples:
            if mytup[0] == "failure":
                modern_country = False

        countries = [x[1] for x in country_tuples]

        # if the country is not modern, has a closing year or does not have a language
        if not modern_country or len(closing_year) >= 1 or language is None:
            print(
                f"skipping {link} because it is closed, has no language, or is not in a modern country"
            )
            return num_created

        defaults = {
            "source_link": link,
            "name": name,
            "countries": countries,
            "description": description,
            "website": website,
            "permid": permid,
            "isin": isin,
            "viafid": viafid,
            "lei": lei,
            "googleid": googleid,
        }

        # filter out unnecessary defaults
        defaults = {k: v for k, v in defaults.items() if v == v and v is not None and v != ""}
        # print(f"updating or creating {link}")
        bank, created = Wikidata.objects.update_or_create(source_id=link, defaults=defaults)
        if created:
            bank.save()

        banks.append(bank)
        num_created += 1 if created else 0
        return num_created

    permid = models.CharField(max_length=15, blank=True)
    isin = models.CharField(max_length=15, blank=True)
    viafid = models.CharField(max_length=15, blank=True)
    lei = models.CharField(max_length=15, blank=True)
    googleid = models.CharField(max_length=15, blank=True)

    countries = CountryField(
        multiple=True, help_text="Where the brand offers retails services", blank=True
    )

    description = models.TextField(
        "Description of this instance of this brand/data source",
        null=True,
        blank=True,
        default="-blank-",
    )

    website = models.URLField(
        "Website of this brand/data source. i.e. bankofamerica.com", null=True, blank=True
    )
