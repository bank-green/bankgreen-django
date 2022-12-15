from django.test import TestCase

import np
import pandas as pd
from brand.models.brand import Brand
from brand.tests.utils import create_test_brands

from datasource.models.usnic import Usnic
from datasource.models.wikidata import Wikidata
from datasource.tests.utils import create_test_usnic

from ..models import Banktrack, Bimpact


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
        self.assertEqual(bank.source_id, "unique_tag")
        self.assertEqual(bank.website, "https://newuri")
        self.assertEqual(bank.countries[0].code, "TW")
        self.assertEqual(bank.source_link, "https://newuri")

        self.assertEqual(bank.subclass().__class__, Banktrack)


class BimpactTestCase(TestCase):
    def setUp(self):
        pass

    def test_no_duplicate_creation_in_load_or_create_individual_instance(self):
        # When a bank with duplicate source_id is sent, it should be merged into an exiing bank
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
                banks=banks, num_created=num_created, row=row
            )

        self.assertEqual(len(Bimpact.objects.all()), 1)

        bank = Bimpact.objects.all()[0]
        self.assertEqual(bank.name, "new_name")
        self.assertEqual(bank.description, "new_description")

        self.assertEqual(bank.source_id, "12345")
        self.assertEqual(bank.website, "https://newuri")
        self.assertEqual(bank.source_link, "https://newuri")


class WikidataTestCase(TestCase):
    def setUp(self):
        pass

    def test_no_duplicate_creation_in_load_or_create_individual_instance(self):
        # When a bank with duplicate source_id is sent, it should be merged into an existing bank
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

        num_created = Wikidata._maybe_create_individual_instance(
            banks=banks, num_created=num_created, df=first
        )

        Wikidata._maybe_create_individual_instance(banks=banks, num_created=num_created, df=second)

        self.assertEqual(len(Wikidata.objects.all()), 1)

        bank = Wikidata.objects.all()[0]
        self.assertEqual(bank.name, "new name")
        self.assertEqual(bank.description, "new_description")

        self.assertEqual(bank.source_id, "http://www.wikidata.org/entity/Q12345")
        self.assertEqual(bank.website, "https://newuri")
        self.assertEqual(bank.source_link, "http://www.wikidata.org/entity/Q12345")


class UsnicTestCase(TestCase):
    fixtures = (
        "fixtures/citieslight/country.json",
        "fixtures/citieslight/region.json",
        # "fixtures/citieslight/subregion.json",
    )

    def setUp(self):
        self.active = pd.read_csv("./datasource/local/usnic/CSV_ATTRIBUTES_ACTIVE_ABRIDGED.CSV")
        self.branches = pd.read_csv("./datasource/local/usnic/CSV_ATTRIBUTES_BRANCHES_ABRIDGED.CSV")
        self.rels = pd.read_csv("./datasource/local/usnic/CSV_RELATIONSHIPS_ABRIDGED.CSV")

    def test_load_or_create_individual_instance(self):
        row = self.active.iloc[47]
        num_created, banks = Usnic._load_or_create_individual_instance(
            banks=[], num_created=0, row=row
        )
        bank = banks[0]

        # make sure it's bank with rssd 71859. Needed for testing since this is a women/minority owned bank
        self.assertEqual(bank.rssd, 71859)
        self.assertEqual(bank.legal_name, "CBW BANK")
        self.assertEqual(bank.name, "CBW BK")
        self.assertEqual(bank.entity_type, "NMB")

        # just one bank created
        self.assertEqual(num_created, 1)
        self.assertEqual(num_created, len(banks))

        # country, region information filled in
        self.assertEqual(bank.country.code, "US")

        # women or minority owned is coded
        self.assertTrue(bank.women_or_minority_owned)

    def test_supplement_with_branch_region_information(self):
        bank_row = self.active[self.active["#ID_RSSD"] == 1164].iloc[0]
        num_created, banks = Usnic._load_or_create_individual_instance(
            banks=[], num_created=0, row=bank_row
        )

        bank = banks[0]

        branch_row = self.branches.iloc[0]
        bank = Usnic._supplement_with_branch_information(branch_row)

        if not bank:
            self.fail("Bank was either not found or created")

        region_abbreviations = [x["geoname_code"] for x in bank.regions.values()]
        self.assertIn("CA", region_abbreviations)

    def test_add_relationships(self):
        # artificially mark all relationships as unended
        self.rels["DT_END"] = 99991231

        # create parent and child bank
        bank_row = self.active[self.active["#ID_RSSD"] == 1155].iloc[0]
        _, child_banks = Usnic._load_or_create_individual_instance(
            banks=[], num_created=0, row=bank_row
        )
        child_bank = child_banks[0]
        parent_bank = Usnic.objects.create(name="test parent", rssd=469951)

        # add relationship info and refresh child. (communication through db)
        Usnic._add_relationships(self.rels)
        child_bank.refresh_from_db()

        # assert that the control json is not default
        self.assertTrue(child_bank.control != {})
        self.assertTrue("469951" in child_bank.control.keys())

    def test_recommend_brands(self):
        brand1, brand2 = create_test_brands()
        usnic1, usnic2, usnic3, usnic4 = create_test_usnic()

        candidate_dict = Usnic.suggest_associations()

        self.assertTrue(brand1 in candidate_dict[usnic1])
        self.assertTrue(brand2 in candidate_dict[usnic2])
        self.assertTrue(brand1 in candidate_dict[usnic3])
        self.assertEqual(len(candidate_dict[usnic4]), 0)
