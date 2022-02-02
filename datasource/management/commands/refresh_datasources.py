from json import load
from django.core.management.base import BaseCommand, CommandError
from datasource.models.banktrack import Banktrack


class Command(BaseCommand):
    help = "refresh data"

    def add_arguments(self, parser):
        parser.add_argument('datasources', nargs='+', type=str, help="the data sources to refresh")
        parser.add_argument(
            '--local',
            help="avoid API calls and load local data where possible. datasources for this option must be specified",
        )

    def handle(self, *args, **options):

        datasources = [x.lower().strip() for x in options['datasources']]
        load_from_api = False if 'all' in options['local'] else True
        if 'all' in datasources or 'banktrack' in datasources:

            if 'banktrack' in options['local']:
                load_from_api = False

            banks, num_created = Banktrack.load_and_create(load_from_api=load_from_api)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully refreshed {len(banks)} banktrack records, creating {num_created} new records"
                )
            )
