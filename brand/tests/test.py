from django.forms import ValidationError
from django.test import TestCase

from brand.models.commentary import Commentary, RatingChoice
from brand.tests.utils import create_test_brands
from datasource.models import Banktrack, Usnic

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
        self.test_usnic1 = Usnic.objects.create(
            source_id="unique_source_id1",
            source_link="abc",
            name="test_bank1",
            website="test_website",
        )
        self.test_usnic2 = Usnic.objects.create(
            source_id="unique_source_id2",
            source_link="abc",
            name="test_bank2",
            website="test_website",
        )
        self.test_usnic3 = Usnic.objects.create(
            source_id="unique_source_id3",
            source_link="abc",
            name="test_bank3",
            website="test_website",
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

    def test_create_brand_from_usnic_new_entry(self):
        # Check that Usnic entry with no corresponding Brand is copied to Brands
        existing_brands, successful_brands = Brand.create_brand_from_usnic(
            Usnic.objects.all().values()[:1]
        )
        self.assertEqual(len(successful_brands), 1)  # Ensure only one entry added
        self.assertEqual(
            len(existing_brands), 0
        )  # Ensure no existing brands found, as usnic should not already be in Brands table

        # Check that only Usnic entry with no corresponding Brands are copied to Brands
        existing_brands, successful_brands = Brand.create_brand_from_usnic(
            Usnic.objects.all().values()[:2]
        )
        self.assertEqual(len(successful_brands), 1)  # Ensure only one new brand created
        self.assertEqual(len(existing_brands), 1)  # Check that existing copy of usnic is ignored

        # Check that no new Brands are created if all Usnic entries selected already exist
        existing_brands, successful_brands = Brand.create_brand_from_usnic(
            Usnic.objects.all().values()[:2]
        )
        self.assertEqual(len(successful_brands), 0)  # Ensure only one new brand created
        self.assertEqual(len(existing_brands), 2)  # Check that existing copies of usnic are ignored


class BrandDatasourceTestCase(TestCase):
    def test_banktrack_brands_can_be_created_from_banktrack(self):
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


class CommentaryTestCase(TestCase):
    def setUp(self) -> None:
        brand1, brand2 = create_test_brands()
        brand3 = Brand.objects.create(
            pk=300,
            tag="another_brand_3",
            name="Another Brand 3",
            aliases="another brand, anotherb",
            website="https://www.anotherbwebaaaasite.com/somepage",
            permid="another permid",
            viafid="another viafid",
            lei="another lei",
            rssd="another rssd",
        )

        brand4 = Brand.objects.create(
            pk=400,
            tag="another_brand_4",
            name="Another Brand 4",
            aliases="another brand, anotherb",
            website="https://www.anotherbwebaaaasite.com/somepage",
            permid="another permid",
            viafid="another viafid",
            lei="another lei",
            rssd="another rssd",
        )

        brand5 = Brand(
            tag="another_brand_5",
            name="Another Brand 5",
            aliases="another brand, anotherb",
            website="https://www.anotherbwebaaaasite.com/somepage",
            permid="another permid",
            viafid="another viafid",
            lei="another lei",
            rssd="another rssd",
        )

        self.commentary1 = Commentary.objects.create(
            brand=brand1, rating=RatingChoice.INHERIT, inherit_brand_rating=None
        )

        self.commentary2 = Commentary.objects.create(
            brand=brand2, rating=RatingChoice.INHERIT, inherit_brand_rating=brand1
        )

        self.commentary3 = Commentary.objects.create(
            brand=brand3, rating=RatingChoice.INHERIT, inherit_brand_rating=brand2
        )

        # brands 4 and 5 point at eachother for their ratings
        self.commentary4 = Commentary.objects.create(brand=brand4, rating=RatingChoice.OK)
        self.commentary5 = Commentary(
            brand=brand5, rating=RatingChoice.INHERIT, inherit_brand_rating=brand4
        )
        self.commentary4.inherit_brand_rating = brand5
        self.commentary4.rating = RatingChoice.INHERIT

    def test_compute_inherited_rating_inherits_from_inherit(self):
        inherited_rating = self.commentary3.compute_inherited_rating()
        self.assertEqual(inherited_rating, RatingChoice.UNKNOWN)

    def test_compute_inherited_rating_happy_path(self):
        self.commentary1.rating = RatingChoice.GREAT
        self.commentary1.save()
        inherited_rating = self.commentary3.compute_inherited_rating(throw_error=True)
        self.assertEqual(inherited_rating, RatingChoice.GREAT)

    def test_compute_inherited_rating_circular_path_raises(self):
        with self.assertRaises(ValidationError):
            self.commentary5.compute_inherited_rating(throw_error=True)

    def test_compute_inherited_rating_circular_path_can_return_unknown(self):
        self.assertEqual(
            self.commentary5.compute_inherited_rating(throw_error=False), RatingChoice.UNKNOWN
        )


class BrandTagTestCase(TestCase):

    # test for a Valid Tag
    def test_brand_valid_tag(self):
        brand1 = Brand(
            name="Test Brand 1",
            tag="Tag_Brand-1"
        )
        # this should not raise any errors
        brand1.save()

    # test for an Invalid Tags
    def test_brand_invalid_tag(self):
        # test case with not allowed characters
        brand1 = Brand(
            name="Test Brand 1",
            tag="TagBrand%$1")

        with self.assertRaises(ValidationError):
            brand1.save()

        # test case with the spaces
        brand1 = Brand(
            name="Test Brand 1",
            tag="Tag Brand 1")

        with self.assertRaises(ValidationError):
            brand1.save()
