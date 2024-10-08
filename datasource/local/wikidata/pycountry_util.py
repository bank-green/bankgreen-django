import pycountry

from .country_map import country_map


def find_country(mystr=None, country_code=None):
    """
    returns a tuple ("status", "normalized country")
    If a country is found, status is "success", if not, it's "failure"
    """

    if mystr is not None and country_map.get(mystr):
        return ("success", country_map.get(mystr))
    if mystr:
        try:
            name = pycountry.countries.search_fuzzy(mystr)[0].name
            return ("success", name)
        except Exception:  # noqa handling noisy data here.
            return ("failure", mystr)
    if country_code:
        try:
            name = pycountry.countries.get(alpha_2=country_code).name
            return ("success", name)
        except Exception:  # noqa handling noisy data here.
            return ("failure", country_code)

    if not mystr and not country_code:
        raise Exception("mystr or country_code must be provided")

    return ("failure", "unknown")
