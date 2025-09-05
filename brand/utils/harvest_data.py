import time
from datetime import datetime, timedelta
from typing import Dict, Union
from urllib.parse import urlencode

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone

import requests


def fetch_harvest_data(
    brand_tag, brand_url="", brand_country="", brand_name="", retry_count=0, max_retries=2
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

        # Explicitly check for 524 and 504 status codes
        if response.status_code in [524, 504]:
            if retry_count < max_retries:
                print(
                    f"Received {response.status_code} status code. Waiting 5 minutes before retry {retry_count + 1}..."
                )
                time.sleep(300)  # 5 minutes = 300 seconds
                return fetch_harvest_data(
                    brand_tag,
                    brand_url,
                    brand_country,
                    brand_name,
                    retry_count=retry_count + 1,
                    max_retries=max_retries,
                )
            else:
                print(f"Max retries reached for {response.status_code} status code")
                return Exception(
                    f"Failed after {max_retries} attempts due to {response.status_code} status code"
                )

        return response.json()

    except Exception as e:
        return e


def fetch_harvest_location_data(
    brand_tag, brand_url="", brand_country="", brand_name="", retry_count=0, max_retries=2
) -> Union[Dict, Exception]:
    base_url = "https://harvest.bank.green/location"

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
        response = requests.get(url, headers={"Authorization": f"Token {settings.HARVEST_TOKEN}"})

        # Explicitly check for 524 and 504 status codes
        if response.status_code in [524, 504]:
            if retry_count < max_retries:
                print(
                    f"Received {response.status_code} status code. Waiting 2 minutes before retry {retry_count + 1}..."
                )
                time.sleep(120)  # 2 minutes = 120 seconds
                return fetch_harvest_location_data(
                    brand_tag,
                    brand_url,
                    brand_country,
                    brand_name,
                    retry_count=retry_count + 1,
                    max_retries=max_retries,
                )
            else:
                print(f"Max retries reached for {response.status_code} status code")
                return Exception(
                    f"Failed after {max_retries} attempts due to {response.status_code} status code"
                )

        response.raise_for_status()
        return response.json()
    except Exception as e:
        return e


def update_commentary_feature_data(commentary, overwrite=False):
    """
    Refresh and persist feature data for the given commentary.
    Returns the saved commentary on success, or None on failure/no-op.
    """
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
            commentary.feature_refresh_date = timezone.now()
            commentary.save()
            return commentary
        else:
            # Gracefully indicate failure; callers can decide how to report it
            return None

    # If not overwriting and no refresh criteria met, treat as no-op
    return None
