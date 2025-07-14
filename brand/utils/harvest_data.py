from datetime import datetime, timedelta
from typing import Dict, Union
from urllib.parse import urlencode

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone

import requests


def fetch_harvest_data(
    brand_tag, brand_url="", brand_country="", brand_name=""
) -> Union[Dict, Exception]:
    base_url = "https://harvest.bank.green/harvest"

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
            url, headers={"Authorization": f"Token {settings.HARVEST_TOKEN}"}, timeout=600
        )

        return response.json()
    except Exception as e:
        return e


def fetch_harvest_location_data(
    brand_tag, brand_url="", brand_country="", brand_name=""
) -> Union[Dict, Exception]:
    base_url = "https:///harvest.bank.green/location"

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
            url, headers={"Authorization": f"Token {settings.HARVEST_TOKEN}"}, timeout=1000
        )
        response.raise_for_status()

        return response.json()
    except Exception as e:
        return e


def update_commentary_feature_data(commentary, overwrite=False) -> None:
    if commentary is None:
        return None

    if (
        overwrite
        # or not commentary.feature_refresh_date
        # or commentary.feature_refresh_date < timezone.now() - timedelta(days=90)
    ):
        data = fetch_harvest_data(
            brand_tag=commentary.brand.tag,
            brand_url=commentary.brand.website,
            brand_country=commentary.brand.countries[0].name if commentary.brand.countries else "",
            brand_name=commentary.brand.name,
        )
        if isinstance(data, dict):
            commentary.feature_json = data
            commentary.feature_refresh_date = datetime.now()
            commentary.save()
        else:
            raise ValidationError({"data": "harvest data needs to be in dict format"})
