import logging
from json import JSONEncoder

import requests

from brand.models import BrandFeature
from brand.models.commentary import InstitutionCredential, InstitutionType


def get_institution_data():
    """
    Retrieve all Institute data from the database.
    """
    return InstitutionType.objects.all(), InstitutionCredential.objects.all()


def concat_brand_feature_data(brand_id):
    """
    Return concatenated brand feature data fieldwise.
    """
    data_dict = {}

    brand_feature_data = BrandFeature.objects.filter(brand_id=brand_id)

    if brand_feature_data:
        data_dict["brand_feature_id"] = ",".join([str(x.id) for x in brand_feature_data])
        data_dict["feature"] = ",".join([str(x.feature) for x in brand_feature_data])

    return data_dict


class PrettyJSONEncoder(JSONEncoder):
    def __init__(self, *args, indent, sort_keys, **kwargs):
        super().__init__(*args, indent=2, sort_keys=False, **kwargs)


def filter_json_field(json_data, filter_value):
    if isinstance(json_data, dict):
        return {
            k: filter_json_field(v, filter_value)
            for k, v in json_data.items()
            if filter_json_field(v, filter_value) is not None
        }
    elif isinstance(json_data, list):
        return [
            filter_json_field(item, filter_value)
            for item in json_data
            if filter_json_field(item, filter_value) is not None
        ]
    elif isinstance(json_data, str) and filter_value.lower() in json_data.lower():
        return json_data
    elif isinstance(json_data, (int, float)) and filter_value.lower() in str(json_data).lower():
        return json_data
    return None


def fetch_cached_harvest_data(tag):
    try:
        response = requests.get(f"https://data.bank.green/api/harvest/{tag}")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Error fetching harvest data for {tag}: {str(e)}")
        raise
