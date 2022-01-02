from json import load
from django.core.management.base import BaseCommand, CommandError
from datasource.models.banktrack import Banktrack


class Command(BaseCommand):
    help = "refresh banktrack data"

    # def add_arguments(self, parser):
    #     parser.add_argument('poll_ids', nargs='+', type=int)

    def handle(self, *args, **options):
        banks = Banktrack.load_and_create(load_from_api=True)
        self.stdout.write(self.style.SUCCESS(f"Successfully refreshed {len(banks)} banktrack data"))
