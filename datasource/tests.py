from re import M

from django.test import TestCase

import pandas as pd

import np
from brand.models.brand import Brand

from datasource.models.wikidata.wikidata import Wikidata

from .models import Banktrack, Bimpact


class BanktrackTestCase(TestCase):
    def setUp(self):
        pass

    def test_no_duplicate_creation_in_load_or_create_individual_instance(self):
        # When a bank with duplicate source_id is sent, it should be merged into an exiing bank
        existing_tags = set()
        banks = []
        num_created = 0
        df = pd.DataFrame(
            [
                {
                    "title": "old_title",
                    "general_comment": "old_comment",
                    "tag": "unique_tag",
                    "link": "https://olduri",
                    "website": "https://olduri",
                    "country": "South Korea",
                    "updated_at": "2020-01-01 00:00:00",
                },
                {
                    "title": "new_title",
                    "general_comment": "new_comment",
                    "tag": "unique_tag",
                    "link": "https://newuri",
                    "website": "https://newuri",
                    "country": "Taiwan, Republic of China",
                    "updated_at": "2020-01-01 00:00:00",
                },
            ]
        )

        for i, row in df.iterrows():
            Banktrack._load_or_create_individual_instance(
                existing_tags=existing_tags, banks=banks, num_created=num_created, row=row
            )

        self.assertEqual(len(Banktrack.objects.all()), 1)

        bank = Banktrack.objects.all()[0]
        self.assertEqual(bank.name, "new_title")
        self.assertEqual(bank.description, "new_comment")
        self.assertEqual(bank.tag, Banktrack.tag_prepend_str + "unique_tag")
        self.assertEqual(bank.source_id, "unique_tag")
        self.assertEqual(bank.website, "https://newuri")
        self.assertEqual(bank.countries[0].code, "TW")
        self.assertEqual(bank.source_link, "https://newuri")


class BimpactTestCase(TestCase):
    def setUp(self):
        pass

    def test_no_duplicate_creation_in_load_or_create_individual_instance(self):
        # When a bank with duplicate source_id is sent, it should be merged into an exiing bank
        existing_tags = set()
        banks = []
        num_created = 0
        df = pd.DataFrame(
            [
                {
                    "company_id": "12345",
                    "company_name": "old_name",
                    "description": "old_description",
                    "b_corp_profile": "https://olduri",
                    "website": "https://olduri",
                    "country": "United States",
                    "date_certified": "2022-01-01",
                },
                {
                    "company_id": "12345",
                    "company_name": "new_name",
                    "description": "new_description",
                    "b_corp_profile": "https://newuri",
                    "website": "https://newuri",
                    "country": "United States",
                    "date_certified": "2022-01-02",
                },
            ]
        )

        for i, row in df.iterrows():
            Bimpact._load_or_create_individual_instance(
                existing_tags=existing_tags, banks=banks, num_created=num_created, row=row
            )

        self.assertEqual(len(Bimpact.objects.all()), 1)

        bank = Bimpact.objects.all()[0]
        self.assertEqual(bank.name, "new_name")
        self.assertEqual(bank.description, "new_description")

        # tag should remain as old tag since the source was updated, newly created
        self.assertEqual(bank.tag, Bimpact.tag_prepend_str + "old_name" + "_" + "12345")
        self.assertEqual(bank.source_id, "12345")
        self.assertEqual(bank.website, "https://newuri")
        self.assertEqual(bank.source_link, "https://newuri")


class WikidataTestCase(TestCase):
    def setUp(self):
        pass

    def test_no_duplicate_creation_in_load_or_create_individual_instance(self):
        # When a bank with duplicate source_id is sent, it should be merged into an existing bank
        existing_tags = set()
        banks = []
        num_created = 0
        first = pd.DataFrame(
            [
                {
                    "bank.value": "http://www.wikidata.org/entity/Q12345",
                    "bankLabel.value": "old name",
                    "bankDescription.value": "old_description",
                    "website.value": "https://olduri",
                    "countryLabel.value": "United States",
                    "instanceLabel.value": "bank",
                    "bankLabel.xml:lang": "en",
                    "permid.value": "abcd",
                    "isin.value": "abcd",
                    "viafid.value": "abcd",
                    "gid.value": "abcd",
                    "lei.value": "abcd",
                    "deathyear.value": np.nan,
                },
                {
                    "bank.value": "http://www.wikidata.org/entity/Q12345",
                    "bankLabel.value": "old name",
                    "bankDescription.value": "old_description",
                    "website.value": "https://olduri",
                    "countryLabel.value": "United States",
                    "instanceLabel.value": "business",
                    "bankLabel.xml:lang": "en",
                    "permid.value": "abcd",
                    "isin.value": "abcd",
                    "viafid.value": "abcd",
                    "gid.value": "abcd",
                    "lei.value": "abcd",
                    "deathyear.value": np.nan,
                },
            ]
        )

        second = pd.DataFrame(
            [
                {
                    "bank.value": "http://www.wikidata.org/entity/Q12345",
                    "bankLabel.value": "new name",
                    "bankDescription.value": "new_description",
                    "website.value": "https://newuri",
                    "countryLabel.value": "Germany",
                    "instanceLabel.value": "commercial bank",
                    "bankLabel.xml:lang": "de",
                    "permid.value": "abcd",
                    "isin.value": "abcd",
                    "viafid.value": "abcd",
                    "gid.value": "abcd",
                    "lei.value": "abcd",
                    "deathyear.value": np.nan,
                },
                {
                    "bank.value": "http://www.wikidata.org/entity/Q12345",
                    "bankLabel.value": "new name",
                    "bankDescription.value": "new_description",
                    "website.value": "https://newuri",
                    "countryLabel.value": "Germany",
                    "instanceLabel.value": "financial institution",
                    "bankLabel.xml:lang": "de",
                    "permid.value": "abcd",
                    "isin.value": "abcd",
                    "viafid.value": "abcd",
                    "gid.value": "abcd",
                    "lei.value": "abcd",
                    "deathyear.value": np.nan,
                },
            ]
        )

        num_created, existing_tags = Wikidata._maybe_create_individual_instance(
            existing_tags=existing_tags, banks=banks, num_created=num_created, df=first
        )

        Wikidata._maybe_create_individual_instance(
            existing_tags=existing_tags, banks=banks, num_created=num_created, df=second
        )

        self.assertEqual(len(Wikidata.objects.all()), 1)

        bank = Wikidata.objects.all()[0]
        self.assertEqual(bank.name, "new name")
        self.assertEqual(bank.description, "new_description")

        # tag should remain as old tag since the source was updated, newly created
        self.assertEqual(bank.tag, Wikidata.tag_prepend_str + "old_name")
        self.assertEqual(bank.source_id, "http://www.wikidata.org/entity/Q12345")
        self.assertEqual(bank.website, "https://newuri")
        self.assertEqual(bank.source_link, "http://www.wikidata.org/entity/Q12345")

    # def test_creates_parent_relationships(self):
    #     df = pd.read_csv("./datasource/wikidata_parent_test.csv")
    #     Wikidata._create(df=df)

    #     askari = Wikidata.objects.get(source_id='http://www.wikidata.org/entity/Q4807137')
    #     bilbao = Wikidata.objects.get(source_id='http://www.wikidata.org/entity/Q806189')
    #     colombia = Wikidata.objects.get(source_id='http://www.wikidata.org/entity/Q16489599')

    #     self.assertIsNotNone(askari)
    #     self.assertIsNotNone(bilbao)
    #     self.assertIsNotNone(colombia)

    #     self.assertIsNone(askari.subsidiary_of_1)

    #     self.assertEqual(colombia.subsidiary_of_1, Brand.objects.get(source_link=bilbao.source_id))
    #     self.assertEqual(colombia.subsidiary_of_1_pct, 100)
