from django.core.management.base import BaseCommand

from brand.models import Commentary
from brand.utils.harvest_data import update_commentary_feature_data


"""
    To be used with cron job, please see GROOT-312 ticket for more context
"""


class Command(BaseCommand):
    help = "Fetches the harvest data of SFI Brands then updates the Brand's Commentary"

    def handle(self, *args, **options):
        self.stdout.write("Fetching Commentaries...")
        sfi_commentaries = Commentary.objects.filter(show_on_sustainable_banks_page=True)
        self.stdout.write(f"Updating {sfi_commentaries.count()} commentaries...")
        success = 0
        failure = 0
        for commentary in sfi_commentaries:
            try:
                result = update_commentary_feature_data(commentary, overwrite=True)
                if result is not None:
                    success += 1
                    self.stdout.write(f"✓ Updated {commentary.brand.tag}")
                else:
                    failure += 1
                    self.stderr.write(f"✗ Skipped/failed {commentary.brand.tag}")
            except Exception as e:
                failure += 1
                self.stderr.write(f"✗ {commentary.brand.tag} failed: {e}")
        self.stdout.write(self.style.SUCCESS(f"Done. Success: {success}, Failed: {failure}"))
