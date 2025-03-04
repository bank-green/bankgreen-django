import logging
from django.core.management.base import BaseCommand
from brand.models import Commentary
from brand.utils.harvest_data import update_commentary_feature_data

"""
    To be used with cron job, please see GROOT-312 ticket for more context
"""


class Command(BaseCommand):
    help = "Fetches the harvest data of SFI Brands then updates the Brand's Commentary"

    def handle(self, *args, **options):
        print("Fetching Commentaries...")
        sfi_commentaries = Commentary.objects.filter(show_on_sustainable_banks_page=True)
        print("Updating commentaries...")
        for commentary in sfi_commentaries:
            try:
                update_commentary_feature_data(commentary, overwrite=True)
            except Exception as e:
                print(f"{commentary.brand.tag} failed...")
                print(e)
