from re import M

from django.test import TestCase

import pandas as pd

from datasource.models.datasource import Datasource

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

    def test_tag_prepend_str_when_accessed_via_a_datasource(self):
        bt = Banktrack.objects.create(
            source_id="unique_source_id",
            # date_updated=datetime.now(),
            source_link="abc",
            name="bt",
            description="test_description",
            website="test_website",
            countries="TW",
            tag=Banktrack.tag_prepend_str + "bt",
        )

        ds_bt = Datasource.objects.all().first()
        prepend_str = ds_bt.tag_prepend_str
        self.assertEqual(prepend_str, 'banktrack_')

class BimpactTextCase(TestCase):
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
