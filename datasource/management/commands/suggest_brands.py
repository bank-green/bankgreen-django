from datetime import datetime, timezone

from django.conf import settings
from django.core.management.base import BaseCommand

import pandas as pd
from airtable import Airtable

from brand.models import Brand, Commentary, RatingChoice
from datasource.models.datasource import Datasource


class Command(BaseCommand):
    help = "suggest brands for each datasource"

    def handle(self, *args, **options):
        datasources = Datasource.objects.all()
        for ds in datasources:
            suggestions = ds.return_suggested_brands_or_datasources()
            # print(f"{ds} suggestions: {suggestions}")
            ds.suggested_brands.set(suggestions)
