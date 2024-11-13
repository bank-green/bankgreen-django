from json import JSONEncoder

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
    if filter_value not in json_data.keys():
        return f"No data available for '{filter_value}' "

    if isinstance(json_data, dict):
        return {filter_value: json_data[filter_value]}
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
