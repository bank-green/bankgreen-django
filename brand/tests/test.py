import json

from django.contrib.auth.models import User
from django.forms import ValidationError
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient

from brand.models.commentary import Commentary, RatingChoice
from brand.models.contact import Contact
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

    def test_feature_override_failure(self):
        """
        Test validation error raised when user tries to update feature_override field with invalid harvest feture yaml.
        """
        brand6 = Brand.objects.create(
            tag="another_brand_6",
            name="Another Brand 6",
            aliases="another brand, anotherb",
            website="https://www.anotherbwebaaaasite.com/somepage",
            permid="another permid",
            viafid="another viafid",
            lei="another lei",
            rssd="another rssd",
        )

        data = {
            "customers_served": {
                "business_and_corporate": {
                    "offered": True,
                    "additional_details": "some additional details",
                    "urls": [],
                }
            }
        }
        with self.assertRaises(ValidationError):
            commentary_obj = Commentary(brand=brand6, feature_override=data)
            commentary_obj.full_clean()

    def test_feature_override_success(self):
        """
        Test commentary object is saved successfully when user tries to update feature_override field with valid harvest feture yaml.
        """
        brand7 = Brand.objects.create(
            tag="another_brand_7",
            name="Another Brand 7",
            aliases="another brand, anotherb",
            website="https://www.anotherbwebaaaasite.com/somepage",
            permid="another permid",
            viafid="another viafid",
            lei="another lei",
            rssd="another rssd",
        )

        data = {
            "customers_served": {
                "corporate": {
                    "offered": True,
                    "additional_details": "some additional details",
                    "urls": [],
                }
            }
        }

        commentary_obj = Commentary(brand=brand7, feature_override=data)
        commentary_obj.full_clean()
        commentary_obj.save()

        self.assertEqual(commentary_obj.feature_override, data)


class BrandTagTestCase(TestCase):
    # test for a Valid Tag
    def test_brand_valid_tag(self):
        brand1 = Brand(name="Test Brand 1", tag="tag_brand-1")
        # this should not raise any errors
        brand1.save()

    # test for an Invalid Tags
    def test_brand_invalid_tag_lowercase_chars(self):
        # test case with not allowed characters
        brand1 = Brand(name="Test Brand 1", tag="tagbrand%$1")

        with self.assertRaises(ValidationError):
            brand1.save()

        # test case with the spaces
        brand1 = Brand(name="Test Brand 1", tag="tag brand 1")

        with self.assertRaises(ValidationError):
            brand1.save()

        # test case with uppercase charachters
        brand1 = Brand(name="Test Brand 1", tag="TagBrand")

        with self.assertRaises(ValidationError):
            brand1.save()


class GetContactsAPITestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super(GetContactsAPITestCase, cls).setUpClass()
        User.objects.create_user(username="test", password="test123")

        brand_obj = Brand.objects.create(name="test_brand", tag="test_tag")
        commentary_obj = Commentary.objects.create(brand=brand_obj)
        Contact.objects.create(
            fullname="test_contact", email="test@contact.com", commentary=commentary_obj
        )

    def setUp(self):
        self.client = APIClient()

    def test_get_contacts(self):
        """
        Test GET /api/bank-contacts API endpoint
        """
        with self.settings(REST_API_CONTACT_SINGLE_TOKEN="XYZSSAAA"):
            token = "XYZSSAAA"
            url = reverse("rest_api:contacts")
            headers = {"HTTP_AUTHORIZATION": f"Token {token}"}
            response = self.client.get(path=url, **headers)
            self.assertEqual(1, len(response.json()))

    def test_get_contacts_filtered_by_brand_tag(self):
        """
        Test GET /api/bank-contacts?brandTag='' API endpoint
        """
        with self.settings(REST_API_CONTACT_SINGLE_TOKEN="XYZSSAAA"):
            token = "XYZSSAAA"
            url = reverse("rest_api:contacts")
            headers = {"HTTP_AUTHORIZATION": f"Token {token}"}
            with self.subTest():
                response = self.client.get(path=url, QUERY_STRING="brandTag=test_tag", **headers)
                self.assertEqual("test@contact.com", response.json()[0]["email"])
                self.assertEqual(200, response.status_code)
            with self.subTest():
                response = self.client.get(path=url, QUERY_STRING="brandTag=xyz", **headers)
                self.assertFalse(len(response.json()), "No contacts available for brandag=test_tag")
                self.assertEqual(200, response.status_code)


class BankAPITestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super(BankAPITestCase, cls).setUpClass()
        User.objects.create_user(username="test", password="test123")
        Brand.objects.create(
            name="Existing bank",
            tag="existing_tag",
            description="Existing Description",
            commentary={"rating": "bad"},
        )


class BankTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.token = "XYZSSAAA"
        self.headers = {
            "content_type": "application/json",
            "HTTP_AUTHORIZATION": f"Token {self.token}",
        }
        # Create an existing brand instance for update tests
        self.existing_brand = Brand.objects.create(
            name="Existing bank", tag="existing_tag", description="Existing Description"
        )
        Commentary.objects.create(
            brand=self.existing_brand, rating="worst", description1="Existing Summary"
        )

    def test_create_bank(self):
        """
        Test PUT /api/bank API endpoint creates a new entry for a non-existing tag
        """
        with self.settings(REST_API_CONTACT_SINGLE_TOKEN=self.token):
            url = reverse("rest_api:bank")
            data = {"name": "New bank", "tag": "new_tag", "commentary": {"rating": "good"}}
            response = self.client.put(path=url, data=json.dumps(data), **self.headers)

            brand_instance = Brand.objects.filter(tag="new_tag")
            self.assertEqual(1, len(brand_instance))
            self.assertEqual("New bank", brand_instance[0].name)
            self.assertEqual("good", brand_instance[0].commentary.rating)

    def test_update_bank(self):
        """
        Test PUT /api/bank API endpoint updates an entry on an existing tag
        """
        with self.settings(REST_API_CONTACT_SINGLE_TOKEN=self.token):
            url = reverse("rest_api:bank")
            data = {
                "name": "Existing bank new name",
                "tag": "existing_tag",
                "commentary": {"rating": "good"},
            }
            response = self.client.put(path=url, data=json.dumps(data), **self.headers)

            brand_instance = Brand.objects.filter(tag="existing_tag")
            # Test that it doesn't make an extra copy
            self.assertEqual(1, len(brand_instance))
            # Test that the name is updated
            self.assertEqual("Existing bank new name", brand_instance[0].name)
            # Test that the commentary object is updated
            self.assertEqual("good", brand_instance[0].commentary.rating)
            # Test that existing data is not overwritten
            self.assertEqual("Existing Summary", brand_instance[0].commentary.description1)
            self.assertEqual("Existing Description", brand_instance[0].description)


class CommentaryFeatureOverrideTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.token = "XYZSSAAA"
        self.headers = {
            "content_type": "application/json",
            "HTTP_AUTHORIZATION": f"Token {self.token}",
        }
        self.mock_feature_override = {
            "customers_served": {
                "corporate": {
                    "additional_details": "some additional details",
                    "offered": True,
                    "urls": [],
                }
            }
        }
        self.existing_brand = Brand.objects.create(
            name="Existing bank", tag="existing_tag", description="Existing Description"
        )
        self.exisitng_commentary = Commentary.objects.create(
            brand=self.existing_brand,
            rating="worst",
            description1="Existing Summary",
            feature_override=self.mock_feature_override,
        )

    def test_get_success(self):
        with self.settings(REST_API_CONTACT_SINGLE_TOKEN=self.token):
            url = reverse(
                "rest_api:commentary_feature_override", kwargs={"pk": self.exisitng_commentary.id}
            )
            response = self.client.get(path=url, **self.headers)
            expected = self.exisitng_commentary.feature_override
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), expected)

    def test_get_missing_commentary_failure(self):
        with self.settings(REST_API_CONTACT_SINGLE_TOKEN=self.token):
            nonexsistant_commentary_id = 9999
            url = reverse(
                "rest_api:commentary_feature_override", kwargs={"pk": nonexsistant_commentary_id}
            )
            response = self.client.get(path=url, **self.headers)
            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.json(), {"error": "Commentary does not exsist"})

    def test_put_combines_feature_success(self):
        valid_feature_data = {
            "policies": {
                "environmental_policy": {
                    "additional_details": "Comprehensive testing on mocking, mockdiversity, and climate stub.",
                    "offered": True,
                    "urls": ["https://www.somebankurl.url/"],
                }
            }
        }
        expected_updated = {**self.mock_feature_override, **valid_feature_data}
        with self.settings(REST_API_CONTACT_SINGLE_TOKEN=self.token):
            url = reverse(
                "rest_api:commentary_feature_override", kwargs={"pk": self.exisitng_commentary.id}
            )
            response = self.client.put(
                path=url, data=json.dumps(valid_feature_data), **self.headers
            )
            updated = Commentary.objects.get(id=self.exisitng_commentary.id)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), expected_updated, updated.feature_override)

    def test_put_creates_feature_success(self):
        with self.settings(REST_API_CONTACT_SINGLE_TOKEN=self.token):
            commentary_without_feature_override = Commentary.objects.create(
                brand=Brand.objects.create(name="b", tag="b", description="d"),
                rating="worst",
                description1="Existing Summary",
            )
            url = reverse(
                "rest_api:commentary_feature_override",
                kwargs={"pk": commentary_without_feature_override.id},
            )
            response = self.client.put(
                path=url, data=json.dumps(self.mock_feature_override), **self.headers
            )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), self.mock_feature_override)

    def test_put_invalid_data_failure(self):
        with self.settings(REST_API_CONTACT_SINGLE_TOKEN=self.token):
            invalid_feature_data = {
                "customers_served": {
                    "business_and_corporate": {
                        "offered": True,
                        "additional_details": "some additional details",
                        "urls": [],
                    }
                }
            }
            url = reverse(
                "rest_api:commentary_feature_override", kwargs={"pk": self.exisitng_commentary.id}
            )
            response = self.client.put(
                path=url, data=json.dumps(invalid_feature_data), **self.headers
            )

            self.assertEqual(response.status_code, 400)
            self.assertEqual(
                response.json(),
                ["Additional properties are not allowed ('business_and_corporate' was unexpected)"],
            )
