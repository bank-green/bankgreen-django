import copy
import json
from typing import Any

from django.contrib.auth.models import User
from django.core.management import call_command
from django.forms import ValidationError
from django.test import TestCase
from django.urls import reverse

import graphene.test
import pandas as pd
from rest_framework.test import APIClient

from brand.models.brand_state import StateLicensed, StatePhysicalBranch
from brand.models.commentary import Commentary, RatingChoice
from brand.models.contact import Contact
from brand.models.state import State
from brand.schema import schema
from brand.tests.test_data.feature_json import dummy_all_features, dummy_no_features
from brand.tests.utils import create_test_brands

from ..models import Brand


class FixtureLoadingTestCase(TestCase):
    def setUp(self):
        pass

    def test_can_import_fixtures(self):
        """
        Verify that it is always possible to import initial.json file
        """
        try:
            call_command("loaddata", "fixtures/initial/initial.json", verbosity=0)
        except Exception as error:
            self.fail(error)


class BrandTestCase(TestCase):
    def setUp(self):
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
                "rest_api:brand_feature_override", kwargs={"brand_id": self.exisitng_commentary.id}
            )
            response = self.client.get(path=url, **self.headers)
            expected = self.exisitng_commentary.feature_override
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), expected)

    def test_get_missing_commentary_failure(self):
        with self.settings(REST_API_CONTACT_SINGLE_TOKEN=self.token):
            nonexsistant_commentary_id = 9999
            url = reverse(
                "rest_api:brand_feature_override", kwargs={"brand_id": nonexsistant_commentary_id}
            )
            response = self.client.get(path=url, **self.headers)
            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.json(), {"error": "Brand's Commentary does not exsist"})

    def test_put_override_feature_success(self):
        with self.settings(REST_API_CONTACT_SINGLE_TOKEN=self.token):
            valid_feature_data = {
                "policies": {
                    "environmental_policy": {
                        "additional_details": "Comprehensive testing on mocking, mockdiversity, and climate stub.",
                        "offered": True,
                        "urls": ["https://www.somebankurl.url/"],
                    }
                }
            }
            url = reverse(
                "rest_api:brand_feature_override", kwargs={"brand_id": self.exisitng_commentary.id}
            )
            response = self.client.put(
                path=url, data=json.dumps(valid_feature_data), **self.headers
            )
            updated = Commentary.objects.get(id=self.exisitng_commentary.id)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), valid_feature_data, updated.feature_override)

    def test_put_creates_feature_success(self):
        with self.settings(REST_API_CONTACT_SINGLE_TOKEN=self.token):
            commentary_without_feature_override = Commentary.objects.create(
                brand=Brand.objects.create(name="b", tag="b", description="d"),
                rating="worst",
                description1="Existing Summary",
            )
            url = reverse(
                "rest_api:brand_feature_override",
                kwargs={"brand_id": commentary_without_feature_override.id},
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
                "rest_api:brand_feature_override", kwargs={"brand_id": self.exisitng_commentary.id}
            )
            response = self.client.put(
                path=url, data=json.dumps(invalid_feature_data), **self.headers
            )

            self.assertEqual(response.status_code, 400)
            self.assertEqual(
                response.json(),
                {
                    "error": [
                        "Additional properties are not allowed ('business_and_corporate' was unexpected)"
                    ]
                },
            )


class BrandStatesTestCase(TestCase):
    def setUp(self) -> None:
        self.usa_state1 = State.objects.create(
            tag="new-hampshire-us", name="Wyoming", country_code="US"
        )
        self.usa_state2 = State.objects.create(tag="alabama-us", name="Alabama", country_code="US")
        self.canada_state = State.objects.create(
            tag="british-columbia-ca", name="British Columbia", country_code="CA"
        )

    def test_adding_brand_states_success(self):
        usa_brand = Brand.objects.create(name="b", tag="b", description="d", countries=["US"])
        StateLicensed.objects.create(brand=usa_brand, state=self.usa_state1)
        StatePhysicalBranch.objects.create(brand=usa_brand, state=self.usa_state1)
        StateLicensed.objects.create(brand=usa_brand, state=self.usa_state2)
        StatePhysicalBranch.objects.create(brand=usa_brand, state=self.usa_state2)
        state_physical_branch = usa_brand.state_physical_branch.all()
        state_licensed = usa_brand.state_licensed.all()
        self.assertEqual(state_licensed[0], self.usa_state2)
        self.assertEqual(state_licensed[1], self.usa_state1)
        self.assertEqual(state_physical_branch[0], self.usa_state2)
        self.assertEqual(state_physical_branch[1], self.usa_state1)

    def test_adding_state_of_wrong_country_raises(self):
        usa_brand = Brand.objects.create(name="b", tag="b", description="d", countries=["US"])
        with self.assertRaises(ValidationError):
            StateLicensed.objects.create(brand=usa_brand, state=self.canada_state)

    def test_adding_same_state_twice_raises(self):
        usa_brand = Brand.objects.create(name="b", tag="b", description="d", countries=["US"])
        StateLicensed.objects.create(brand=usa_brand, state=self.usa_state1)
        with self.assertRaises(ValidationError):
            StateLicensed.objects.create(brand=usa_brand, state=self.usa_state1)


class TestUpdateContacts(TestCase):
    def setUp(self):
        self.brand = Brand.objects.create(tag="test_brand", name="Test Brand")
        self.commentary = Commentary.objects.create(brand=self.brand)
        Contact.objects.all().delete()

    def test_update_contacts_command(self):
        contact_model_length_before = len(list(Contact.objects.all()))
        # Simulate command execution
        csv_path = "brand/tests/test_data/contacts.csv"
        df = pd.read_csv(csv_path)
        for _, row in df.iterrows():
            if Contact.objects.filter(email=row["email"]):
                continue
            try:
                commentary_obj = Commentary.objects.get(brand__tag=row["brand_tag"])
            except Commentary.DoesNotExist:
                commentary_obj = None
            Contact.objects.create(
                fullname=row["fullname"], email=row["email"], commentary=commentary_obj
            )
        contact_model_length_after = len(list(Contact.objects.all()))
        self.assertNotEqual(contact_model_length_before, contact_model_length_after)
        contact1 = Contact.objects.get(email="johndoe@testbrand.com")
        self.assertEqual(contact1.fullname, "John Doe")
        self.assertEqual(contact1.commentary, self.commentary)
        contact2 = Contact.objects.get(email="janeastrid@testbrand.com")
        self.assertEqual(contact2.fullname, "Jane Astrid")
        self.assertEqual(contact2.commentary, self.commentary)


class BrandsFilterHarvestDataTest(TestCase):
    """
    Tests for `resolve_brands` and `harvest_data_filter_q` brands filter functionalty
    Found in brand's Schema.py
    As needed for the FE's sustainable-eco-banks page
    """

    def setUp(self) -> None:
        Brand.objects.create(tag=f"normal_brand")

        for n in range(2):
            b = Brand.objects.create(tag=f"brand_with_empty_features_json{n}")
            Commentary.objects.create(brand=b)

        for n in range(2):
            b = Brand.objects.create(tag=f"brand_with_all_features{n}")
            Commentary.objects.create(brand=b, feature_json=dummy_all_features)

        for n in range(2):
            b = Brand.objects.create(tag=f"brand_offering_no_features{n}")
            Commentary.objects.create(brand=b, feature_json=dummy_no_features)

        dummy_partial_features = copy.deepcopy(dummy_all_features)
        dummy_partial_features["customers_served"]["corporate"]["offered"] = False
        dummy_partial_features["deposit_products"]["checkings_or_current"]["offered"] = False
        del dummy_partial_features["services"]

        for n in range(2):
            b = Brand.objects.create(tag=f"brand_with_partial_features{n}")
            Commentary.objects.create(brand=b, feature_json=dummy_partial_features)

        self.gql_client = graphene.test.Client(schema)

    def test_filters_successfully(self):
        variables = {
            "harvestData": {
                "customersServed": ["corporate", "sme", "retail_and_individual"],
                "depositProducts": ["checkings_or_current", "savings", "CDs"],
                "services": ["mobile_banking", "ATM_network", "local_branches"],
                "loanProducts": [
                    "corporate_lending",
                    "small_business_lending",
                    "equipment_lending",
                ],
            }
        }

        query = """
        query FilterBrands($harvestData: HarvestDataFilterInput) {
            brands(harvestData: $harvestData) {
                edges {
                    node {
                        tag
                        harvestData {
                            customersServed
                            depositProducts
                            services
                            financialFeatures
                        }
                    }
                }
            }
        }
        """

        res: Any = self.gql_client.execute(query, variables=variables)
        res = res["data"]["brands"]["edges"]

        self.assertEqual(len(res), 2)
        for r in res:
            data = r["node"]["harvestData"]
            expected_fields = {
                "customersServed",
                "depositProducts",
                "services",
                "financialFeatures",
            }
            self.assertTrue(expected_fields.issubset(data.keys()))

    def test_filters_partials_successfully(self):
        variables = {
            "harvestData": {
                "customersServed": ["sme", "retail_and_individual"],
                "depositProducts": ["savings", "CDs"],
            }
        }

        query = """
        query FilterBrands($harvestData: HarvestDataFilterInput) {
            brands(harvestData: $harvestData) {
                edges {
                    node {
                        tag
                    }
                }
            }
        }
        """

        res: Any = self.gql_client.execute(query, variables=variables)
        res = res["data"]["brands"]["edges"]

        self.assertEqual(len(res), 4)

    def test_doesnt_filter_when_not_invoked(self):
        variables = {}

        query = """
        query FilterBrands($harvestData: HarvestDataFilterInput) {
            brands(harvestData: $harvestData) {
                edges {
                    node {
                        tag
                        harvestData {
                            customersServed
                            depositProducts
                            services
                            financialFeatures
                        }
                    }
                }
            }
        }
        """

        res: Any = self.gql_client.execute(query, variables=variables)
        res = res["data"]["brands"]["edges"]

        self.assertEqual(len(res), 9)
