from django.core.management.base import BaseCommand

import pandas as pd

from brand.models import Brand, Commentary, Contact


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("contacts_file", help="Contacts file path (CSV) ")

    def handle(self, *args, **options):
        # Read notion contacts.csv file
        contact_csv_file_path = options["contacts_file"]
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
