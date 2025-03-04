from django.core.management.base import BaseCommand
from brand.models import Commentary
from brand.utils.harvest_data import update_commentary_feature_data


class Command(BaseCommand):
    help = "Fetches the harvest data of SFI Brands then updates the Brand's Commentary"

    def handle(self, *args, **options):
        sfi_commentaries = Commentary.objects.filter(show_on_sustainable_banks_page=True)
        for commentary in sfi_commentaries:
            update_commentary_feature_data(commentary, overwrite=True)
