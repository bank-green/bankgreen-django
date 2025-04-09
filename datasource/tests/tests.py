from django.core.management import call_command
from django.test import TestCase

import np
import pandas as pd

from brand.models import Brand
from brand.models.contact import Commentary, Contact
from brand.tests.utils import create_test_brands


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


class TestUpdateContacts(TestCase):
    def setUp(self):
        self.brand = Brand.objects.create(tag="test_brand", name="Test Brand")
        self.commentary = Commentary.objects.create(brand=self.brand)
        Contact.objects.all().delete()

    def test_update_contacts_command(self):
        contact_model_length_before = len(list(Contact.objects.all()))
        # Simulate command execution
        csv_path = "datasource/tests/test_data/contacts.csv"
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
