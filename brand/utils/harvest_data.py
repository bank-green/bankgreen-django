import requests
from datetime import datetime, timedelta
from django.conf import settings
from urllib.parse import quote

def fetch_harvest_data(brand_tag, brand_url="", brand_country="", brand_name=""):
    base_url = "https://bank.green/harvest"
    
    params = {
        "bankTag": brand_tag,
        "bankUrl": brand_url,
        "bankCountry": brand_country,
        "bankName": brand_name
    }
    
    # URL encode the parameters
    encoded_params = "&".join(f"{k}={quote(v)}" for k, v in params.items() if v)
    
    url = f"{base_url}?{encoded_params}"
    
    response = requests.get(url, headers={
        "Authorization": f"Token {settings.HARVEST_API_TOKEN}"
    })
    
    if response.status_code == 200:
        return response.json()
    else:
        return None

def update_commentary_feature_data(commentary, overwrite=False):
    if overwrite or not commentary.feature_refresh_date or commentary.feature_refresh_date < datetime.now() - timedelta(days=90):
        data = fetch_harvest_data(
            brand_tag=commentary.brand.tag,
            brand_url=commentary.brand.website,
            brand_country=commentary.brand.countries[0].name if commentary.brand.countries else "",
            brand_name=commentary.brand.name
        )
        if data:
            commentary.feature_json = data
            commentary.feature_refresh_date = datetime.now()
            commentary.save()