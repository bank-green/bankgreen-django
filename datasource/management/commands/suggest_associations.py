import time

from django.core.management.base import BaseCommand

from datasource.models.usnic import Usnic


class Command(BaseCommand):
    help = "suggest brands for each datasource"

    def handle(self, *args, **options):
        print("Suggesting Associations between brands and USNIC objects... ")
        start = time.time()
        suggested_associations = Usnic.suggest_associations()
        end = time.time()

        print(suggested_associations)

        print(f"Suggesting Associations complete.\n\nTime elapsed in minutes: {(end - start)/60}")
