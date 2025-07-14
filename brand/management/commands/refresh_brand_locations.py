from django.core.management.base import BaseCommand

from brand.models import Brand, State
from brand.utils.harvest_data import fetch_harvest_location_data


"""
    To be used with cron job, ran ever 3 month
    please see GROOT-414 ticket for more context
"""


class Command(BaseCommand):
    help = "For US/CA/AU countries, this refreshes their state information using harvest"
    countries = ["AU", "US", "CA"]

    def handle(self, *args, **options):
        brands_by_country = dict()

        # the harvest location url endpoint only takes one country at a time
        for c in self.countries:
            brands_by_country[c] = Brand.objects.filter(countries__contains=[c])

        print(f"Fetching and updating state for  countries...")
        for country, brands in brands_by_country:
            for brand in brands:
                print(f"Attempt for: {brand.tag}, {country}")
                data = fetch_harvest_location_data(
                    brand_tag=brand.tag,
                    brand_url=brand.website,
                    brand_country=country,
                    brand_name=brand.name,
                )

                if isinstance(data, Exception):
                    print(f"Error: {brand.tag}, failed to fetch:", data)
                    continue

                location_data = data.get("location")
                if not location_data:
                    print(f"Error: {brand.tag}: missing location data")
                    continue

                state_licensed = location_data.get("licensed_to_operate_in")
                state_physical_branch = location_data.get("physical_branches")

                for state_code in state_licensed or []:
                    state = State.objects.filter(tag=state_code).first()
                    if not state:
                        continue
                    brand.state_licensed.add(state)

                for state_code in state_physical_branch or []:
                    state = State.objects.filter(tag=state_code).first()
                    if not state:
                        continue
                    brand.state_physical_branch.add(state)
