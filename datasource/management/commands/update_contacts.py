from django.core.management.base import BaseCommand
from brand.models import Contact
from brand.models import Brand, Contact, Commentary
import pandas as pd


class Command(BaseCommand):
    def handle(self, *args, **options):
        # Read notion contacts.csv file
        contact_csv_file_path = "fixtures/contacts.csv"
        df = pd.read_csv(contact_csv_file_path)

        # update contact model
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
