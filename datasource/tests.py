from django.test import TestCase
from .models import Banktrack

import pandas as pd


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
                    "updated_at": "2020-01-01 00:00:00",
                },
                {
                    "title": "new_title",
                    "general_comment": "new_comment",
                    "tag": "unique_tag",
                    "link": "https://newuri",
                    "website": "https://newuri",
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
        self.assertEqual(bank.source_link, "https://newuri")
