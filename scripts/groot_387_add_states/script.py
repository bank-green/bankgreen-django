"""
to run:
django shell < scripts/groot_387_add_states/script.py
"""

from django.db.models import Count

from cities_light.models import Region

from brand.models.brand import Brand
from brand.models.brand_state import StateLicensed
from brand.models.state import State


usa_state_data = Region.objects.filter(country_id=234)
canada_state_data = Region.objects.filter(country_id=38)
australia_state_data = Region.objects.filter(country_id=13)

# Populate our State Model for USA, Canada, and Australia
for [country_code, states] in [
    ["US", usa_state_data],
    ["CA", canada_state_data],
    ["AU", australia_state_data],
]:
    for state in states:
        State.objects.create(
            tag=f"{state.slug}-{country_code.lower()}",
            name=state.name_ascii,
            country_code=country_code,
        )


# Migrate brands with state data from "Regions" to StateLicensed
brands_with_regions = Brand.objects.annotate(num_r=Count("regions")).filter(num_r__gt=0)

for brand in brands_with_regions:
    for region in brand.regions.all():
        if region.country.code2 in {"US", "CA", "AU"}:
            tag = f"{region.country.code2.lower()}-{region.slug}"
            state = State.objects.get(tag=tag)
            StateLicensed.objects.create(brand=brand, state=state)
