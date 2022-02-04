from datetime import datetime
from django.test import TestCase
from .models import Brand
from datasource.models import Banktrack


import pandas as pd


class BrandTestCase(TestCase):
    def setUp(self):
        self.test_bank = Banktrack.objects.create(
            source_id='unique_source_id',
            # date_updated=datetime.now(),
            source_link='abc',
            name='test_bank',
            description='test_description',
            website='test_website',
            tag=Banktrack.tag_prepend_str + 'unique_source_id',
        )

    def test_create_brand_from_datasource(self):
        # When a bank with duplicate source_id is sent, it should be merged into an exiing bank
        brands_created, brands_updated = Brand.create_brand_from_datasource([self.test_bank])
        self.assertEqual(len(brands_created), 1)
        self.assertEqual(len(brands_updated), 0)
        self.assertEqual(brands_created[0].name, 'test_bank')
        self.assertEqual(brands_created[0].tag, 'unique_source_id')
        self.assertEqual(brands_created[0].description, 'test_description')

        # test re-creating brands to see whether they are returned as updated
        brands_created, brands_updated = Brand.create_brand_from_datasource([self.test_bank])
        self.assertEqual(len(brands_created), 0)
        self.assertEqual(len(brands_updated), 1)
        self.assertEqual(brands_updated[0].name, 'test_bank')
        self.assertEqual(brands_updated[0].tag, 'unique_source_id')
        self.assertEqual(brands_updated[0].description, 'test_description')
