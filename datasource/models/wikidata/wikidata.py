
import traceback
from qwikidata.sparql import return_sparql_query_results

import pandas as pd
import np

from datasource.models.datasource import Datasource
from .pycountry_util import find_country

class Wikidata(Datasource):
    """
    Wikidata has a community sourced dataset of banks, various unique identifiers, and their countries of operation.
    Data is collected via the Wikidata.org api. The API sometimes times out when hit too often, so be sure not to
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
            print("Loading Wikidata data from API...")
            with open('./datasource/models/wikidata/query.sparql') as query_file:
                myquery = query_file.read()
            res = return_sparql_query_results(myquery)
            df = pd.json_normalize(res['results']['bindings'])
            df.to_csv('./datasource/local/wikidata/wikidata.csv')
        
        return cls._create(df)
    
    @classmethod
    def _create(cls, df):
        # remove all parent/subsidiary_of relationships that are not banks.
        bank_values = set(df['bank.value'])

        def only_allowed(val):
            if val in bank_values:
                return val
            return np.nan
        df['parent.value'] = df['parent.value'].apply(only_allowed)

        # cycle through banks and add them, temporarily ignoring parent relationships
        existing_tags = {x.tag for x in cls.objects.all()}
        banks = []
        num_created = 0
        bank_values = set(df['bank.value'])
        for bank_value in bank_values:
            bank_df = df[df['bank.value'] == bank_value]

            try:
                num_created, existing_tags = cls._maybe_create_individual_instance(
                    existing_tags, banks, num_created, bank_df
                )
            except Exception as e:
                print("\n\n===Wikidata failed creation or updating===\n\n")
                print(bank_value)
                print(bank_df)
                print(e)
                traceback.print_exc()
            

        def add_subsidiary(bank, parent):
            print(f'adding parent {parent.tag} to child {bank.tag}')
            if not bank.subsidiary_of_1:
                bank.subsidiary_of_1 = parent
                return bank.save()
            if not bank.subsidiary_of_2:
                bank.subsidiary_of_2 = parent
                return bank.save()
            if not bank.subsidiary_of_3:
                bank.subsidiary_of_3 = parent
                return bank.save()
            if not bank.subsidiary_of_4:
                bank.subsidiary_of_4 = parent
                return bank.save()

        for bank_obj in Wikidata.objects.all():
            bank_df = df[df['bank.value'] == bank_obj.source_id]
            parent_links = {x for x in set(bank_df['parent.value']) if x == x}
            for parent_link in parent_links:
                parent_objs = Wikidata.objects.filter(source_id=parent_link)
                if parent_objs.exists():
                    add_subsidiary(bank_obj, parent_objs[0])
        return banks, num_created

    @classmethod
    def _generate_tag(cls, wd_tag, increment=0, existing_tags=None):
        og_tag = wd_tag

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
    def _maybe_create_individual_instance(cls, existing_tags, banks, num_created, df):
        """
        Parse a dataframe looking for the bank uri. Extract values from it and instantiate a bank
        if the bank is probably a modern one.
        """
        # get a single name for the bank
        name = cls._random_element_or_none(df['bankLabel.value'])
        if name is None:
            print(f'skipping {link} because it has no name')
            return num_created, existing_tags

        wd_tag = name.lower().strip().replace(" ", "_")

        # generate tag
        tag = cls._generate_tag(wd_tag = wd_tag, existing_tags = existing_tags)

        # get the languages of the name
        language = cls._random_element_or_none(df['bankLabel.xml:lang'])
        website = cls._random_element_or_none(df['website.value'])

        countries = set(df['countryLabel.value'])
        countries = {x for x in countries if x == x}

        # get the identifiers
        permid = cls._random_element_or_none(df['permid.value'])
        isin = cls._random_element_or_none(df['isin.value'])
        viafid = cls._random_element_or_none(df['viafid.value'])
        lei = cls._random_element_or_none(df['lei.value'])
        # unclear why, but qwikidata falls over when using ?googleid as a parm. use gid instead.
        googleid = cls._random_element_or_none(df['gid.value'])

        # get random description
        description = cls._random_element_or_none(
            df['bankDescription.value'])

        link = cls._random_element_or_none(df['bank.value'])

        # used only for excluding banks that have been closed
        closing_year = (df['deathyear.value'])
        closing_year = {x for x in closing_year if x == x}

        # is the bank's country current or historical?
        # if it's a historical country, don't add to the dataset
        country_tuples = [find_country(x) for x in countries]

        modern_country = True
        for mytup in country_tuples:
            if mytup[0] == 'failure':
                modern_country = False

        countries = [x[1] for x in country_tuples]

        # if the country is not modern, has a closing year or does not have a language
        if not modern_country or len(closing_year) >= 1 or language is None:
            print(f'skipping {link} because it is closed, has no language, or is not in a modern country')
            return num_created, existing_tags

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
            "googleid": googleid
        }

        # filter out unnecessary defaults
        defaults = {k: v for k, v in defaults.items() if v == v and v is not None and v != ""}
        print(f'updating or creating {link}')
        bank, created = Wikidata.objects.update_or_create(source_id = link, defaults=defaults )
        if created:
            bank.tag = tag
            bank.save()

        banks.append(bank)
        num_created += 1 if created else 0
        existing_tags.add(tag)
        return num_created, existing_tags