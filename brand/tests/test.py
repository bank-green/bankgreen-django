from django.test import TestCase
from brand.tests.utils import create_test_brands

from datasource.models import Banktrack

from ..models import Brand


class BrandTestCase(TestCase):
    def setUp(self):
        self.test_banktrack = Banktrack.objects.create(
            source_id="unique_source_id",
            source_link="abc",
            name="test_bank",
            description="test_description",
            website="test_website",
            countries="TW",
            tag=Banktrack.tag_prepend_str + "unique_source_id",
        )
        self.brand1, self.brand2 = create_test_brands()

    def test_create_spelling_dictionary(self):
        spelling_dict = Brand.create_spelling_dictionary()
        # print(spelling_dict)

        self.assertTrue(spelling_dict.get("test brand 1"), 100)
        self.assertTrue(spelling_dict.get("test brand"), 100)
        self.assertTrue(spelling_dict.get("testb"), 100)
        self.assertTrue(spelling_dict.get("tb1"), 100)
        self.assertTrue(spelling_dict.get("tb"), 100)
        self.assertTrue(spelling_dict.get("testbrand.com"), 100)
        self.assertTrue(spelling_dict.get("another rssd"), 100)

        self.assertTrue(spelling_dict.get("another brand 2"), 200)
        self.assertTrue(spelling_dict.get("another brand"), 200)
        self.assertTrue(spelling_dict.get("anotherb"), 200)
        self.assertTrue(spelling_dict.get("ab2"), 200)
        self.assertTrue(spelling_dict.get("ab"), 200)
        self.assertTrue(spelling_dict.get("anotherbwebsite.com"), 200)
        self.assertTrue(spelling_dict.get("anotherbwebsite.com/somepage"), 200)
        self.assertTrue(spelling_dict.get("another lei"), 200)

    def test_create_brand_from_banktrack(self):
        # When a bank with duplicate source_id is sent, it should be merged into an existing bank
        brands_created, brands_updated = Brand.create_brand_from_banktrack([self.test_banktrack])
        self.assertEqual(len(brands_created), 1)
        self.assertEqual(len(brands_updated), 0)
        self.assertEqual(brands_created[0].name, "test_bank")
        self.assertEqual(brands_created[0].tag, "unique_source_id")
        self.assertEqual(brands_created[0].countries[0].code, "TW")
        self.assertEqual(brands_created[0].description, "test_description")

        # test re-creating brands to see whether they are returned as updated
        brands_created, brands_updated = Brand.create_brand_from_banktrack([self.test_banktrack])
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
            source_link="abc",
            name="matched_banktrack",
            description="test_description",
            website="test_website",
            countries="TW",
            tag=Banktrack.tag_prepend_str + "kinged_fred",
        )
        brands_created, _ = Brand.create_brand_from_banktrack([self.kinged_fred])
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


# commented out until we finish reworking the brand-datasource association
#
#     def test_suggesting_datasources_from_a_brand(self):
#         suggested_datasources = self.brand.return_suggested_brands_or_datasources()

#         # already associated datasources should not be in suggested
#         self.assertTrue(self.kinged_fred not in suggested_datasources)

#         # brands should not be in suggested
#         self.assertTrue(self.brand not in suggested_datasources)

#         # some datasources should not match and should not be suggested
#         self.assertTrue(self.sad_aborted_pawn not in suggested_datasources)

#         # similarly named datasources should be in suggested_datasources
#         self.assertTrue(self.pending_king_george in suggested_datasources)

#         # def test_suggesting_brands_from_a_datasource(self):
#         suggested_brands = self.pending_king_george.return_suggested_brands_or_datasources()

#         self.assertTrue(self.brand in suggested_brands)

#         # non-brands should not be suggested
#         self.assertListEqual([], [x for x in suggested_brands if x.__class__ != Brand])

#         # datasources should not recommend themselves
#         self.assertTrue(self.pending_king_george not in suggested_brands)
