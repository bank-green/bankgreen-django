from brand.models import Brand
from datasource.models import Banktrack, Bimpact
from django.core.management.base import BaseCommand


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

        if 'all' in datasources or 'banktrack' in datasources:
            self.refresh_banktrack(options)

        if 'all' in datasources or 'bimpact' in datasources:
            self.refresh_bimpact(options)

    def refresh_bimpact(self, options):
        load_from_api = False if options['local'] and 'all' in options['local'] else True
        if options['local'] and 'banktrack' in options['local']:
            load_from_api = False

        banks, num_created = Bimpact.load_and_create(load_from_api=load_from_api)
        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully refreshed {len(banks)} bimpact records, creating {num_created} new records\n"
            )
        )

        # Do not automatically create brands from banktrack because this should be a manual process
        # brands_created, brands_updated = Brand.create_brand_from_datasource(banks)
        # self.output_brand_creation(brands_created, brands_updated, Bimpact)

    def refresh_banktrack(self, options):
        load_from_api = False if options['local'] and 'all' in options['local'] else True
        if options['local'] and 'banktrack' in options['local']:
            load_from_api = False

        banks, num_created = Banktrack.load_and_create(load_from_api=load_from_api)
        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully refreshed {len(banks)} banktrack records, creating {num_created} new records\n"
            )
        )

        brands_created, brands_updated = Brand.create_brand_from_datasource(banks)
        self.output_brand_creation(brands_created, brands_updated, Banktrack)

    def output_brand_creation(self, brands_created, brands_updated, datasource_class):
        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully created {len(brands_created)} brands from {datasource_class}: {', '.join([x.tag for x in brands_created])}\n"
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully updated {len(brands_updated)} brands from {datasource_class}: {', '.join([x.tag for x in brands_updated])}\n"
            )
        )
