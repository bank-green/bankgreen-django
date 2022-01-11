from json import load
from django.core.management.base import BaseCommand, CommandError
from datasource.models.banktrack import Banktrack


class Command(BaseCommand):
    help = "refresh data"

    def add_arguments(self, parser):
        parser.add_argument('datasources', nargs='+', type=str, help="the data source to refresh")
        # parser.add_argument('--local', action='')

    def handle(self, *args, **options):

        datasources = [x.lower().strip() for x in options['datasources']]
        if 'banktrack' in datasources:
            banks, num_created = Banktrack.load_and_create(load_from_api=False)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully refreshed {len(banks)} banktrack records, creating {num_created} new records"
                )
            )
