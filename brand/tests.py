from datetime import datetime

from django.test import TestCase

import pandas as pd

from datasource.models import Banktrack

from .models import Brand


class BrandTestCase(TestCase):
    def setUp(self):
        self.test_bank = Banktrack.objects.create(
            source_id="unique_source_id",
            # date_updated=datetime.now(),
            source_link="abc",
            name="test_bank",
            description="test_description",
            website="test_website",
            countries="TW",
            tag=Banktrack.tag_prepend_str + "unique_source_id",
        )

    def test_create_brand_from_datasource(self):
        # When a bank with duplicate source_id is sent, it should be merged into an exiing bank
        brands_created, brands_updated = Brand.create_brand_from_datasource([self.test_bank])
        self.assertEqual(len(brands_created), 1)
        self.assertEqual(len(brands_updated), 0)
        self.assertEqual(brands_created[0].name, "test_bank")
        self.assertEqual(brands_created[0].tag, "unique_source_id")
        self.assertEqual(brands_created[0].countries[0].code, "TW")
        self.assertEqual(brands_created[0].description, "test_description")

        # test re-creating brands to see whether they are returned as updated
        brands_created, brands_updated = Brand.create_brand_from_datasource([self.test_bank])
        self.assertEqual(len(brands_created), 0)
        self.assertEqual(len(brands_updated), 1)
        self.assertEqual(brands_updated[0].name, "test_bank")
        self.assertEqual(brands_updated[0].tag, "unique_source_id")
        self.assertEqual(brands_updated[0].countries[0].code, "TW")
        self.assertEqual(brands_updated[0].description, "test_description")


class BrandDatasourceTestCase(TestCase):
    def setUp(self):
        self.kinged_fred = Banktrack.objects.create(
            source_id="kinged_fred",
            # date_updated=datetime.now(),
            source_link="abc",
            name="matched_banktrack",
            description="test_description",
            website="test_website",
            countries="TW",
            tag=Banktrack.tag_prepend_str + "kinged_fred",
        )
        brands_created, _ = Brand.create_brand_from_datasource([self.kinged_fred])
        self.brand = brands_created[0]

        self.pending_king_george = Banktrack.objects.create(
            source_id="pending_king_george",
            source_link="abcdef",
            name="Matched banktrack",
            description="test_description",
            website="test_website",
            countries="TW",
            tag=Banktrack.tag_prepend_str + "pending_king_george",
        )

        self.sad_aborted_pawn = Banktrack.objects.create(
            source_id="test_non_matched_banktrack_source_id",
            source_link="abc",
            name="test_non_matched_banktrack",
            description="test_description",
            website="test_website",
            countries="TW",
            tag=Banktrack.tag_prepend_str + "sad_aborted_pawn",
        )

    def test_correct_banks_are_matched(self):
        suggested_datasources = self.brand.datasource_suggestions()

        # already associated datasources should not be in suggested
        self.assertTrue(self.kinged_fred not in suggested_datasources)

        # brands should not be in suggested
        self.assertTrue(self.brand not in suggested_datasources)

        # some datasources should not match and should not be suggested
        self.assertTrue(self.sad_aborted_pawn not in suggested_datasources)

        # similarly named datasources should be in suggested_datasources
        self.assertTrue(self.pending_king_george in suggested_datasources)
