from datetime import datetime, timedelta
from typing import Dict, Union
from urllib.parse import urlencode

from django.conf import settings

import requests


def fetch_harvest_data(
    brand_tag, brand_url="", brand_country="", brand_name=""
) -> Union[Dict, Exception]:
    base_url = "https://bank.green/harvest"

    params = {
        "bankTag": brand_tag,
        "bankUrl": brand_url,
        "bankCountry": brand_country,
        "bankName": brand_name,
    }

    # URL encode the parameters
    encoded_params = urlencode(params, doseq=True)

    url = f"{base_url}?{encoded_params}"

    try:
        response = requests.get(
            url,
            headers={"Authorization": f"Token {settings.REST_API_CONTACT_SINGLE_TOKEN}"},
            timeout=600,
        )

        return response.json()
    except Exception as e:
        return e


def update_commentary_feature_data(commentary, overwrite=False):
    if (
        overwrite
        or not commentary.feature_refresh_date
        or commentary.feature_refresh_date < datetime.now() - timedelta(days=90)
    ):
        data = fetch_harvest_data(
            brand_tag=commentary.brand.tag,
            brand_url=commentary.brand.website,
            brand_country=commentary.brand.countries[0].name if commentary.brand.countries else "",
            brand_name=commentary.brand.name,
        )
        if data:
            commentary.feature_json = data
            commentary.feature_refresh_date = datetime.now()
            commentary.save()
