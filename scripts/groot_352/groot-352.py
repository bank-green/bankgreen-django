import json
import os
import re
from datetime import datetime
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.utils import timezone

import requests
from dotenv import load_dotenv

from brand.models import *
from brand.models.commentary import InstitutionType


ENV_DIR = str(Path().cwd() / "bankgreen/.env")
load_dotenv(ENV_DIR)


"""
    This script enters information from usnic into brands for FCU entity type
    The Datasource model and its children (including the USNICS model) were removed in 
    GROOT-347 so expect this command to break.
"""


def check_website_URL(url):
    if not url:
        return None
    validator = URLValidator()
    try:
        validator(url)
        return url
    except ValidationError:
        url = "https://" + url

    try:
        validator(url)
    except ValidationError:
        return None


def find_website(fcu_name):
    url = "https://api.perplexity.ai/chat/completions"

    payload = {
        "model": "sonar",
        "messages": [
            {"role": "system", "content": "return only a url."},
            {"role": "user", "content": f"Return this credit union's website {fcu_name}"},
        ],
        "max_tokens": 15,
        "temperature": 0.2,
        "top_p": 0.9,
        "top_k": 0,
        "stream": False,
        "presence_penalty": 0,
        "frequency_penalty": 1,
    }
    headers = {
        "Authorization": f"Bearer {os.environ['PERPLEXITY_KEY']}",
        "Content-Type": "application/json",
    }

    response = requests.request("POST", url, json=payload, headers=headers)
    url = json.loads(response.text)["choices"][0]["message"]["content"]
    return url


def generate_tag(bt_tag, increment=0, existing_tags=None):
    og_tag = bt_tag
    # memoize existing tags for faster recursion
    if increment < 1:
        bt_tag = og_tag
    else:
        bt_tag = og_tag + "_" + str(increment).zfill(2)

    if bt_tag not in existing_tags:
        return bt_tag
    else:
        return generate_tag(og_tag, increment=increment + 1, existing_tags=existing_tags)


print("Running db_changes_fcu.py")
rssd_ids = []
with open(r"datasource/management/commands/cdfi_rssd_numbers.txt", "r") as file:
    rssd_ids = {line.strip() for line in file}
filtered_usnic = Usnic.objects.filter(
    entity_type="FCU"
).values(  # Note: Usnic will be undefined # type: ignore
    "ncua",
    "website",
    "country",
    "legal_name",
    "rssd",
    "lei",
    "fdic_cert",
    "ein",
    "occ",
    "thrift_hc",
    "cusip",
)


# selects the two fields to check for duplicates
brand_values = Brand.objects.values("tag", "name")
existing_tags = {x["tag"] for x in brand_values}
existing_names = {x["name"] for x in brand_values}

fcu = InstitutionType.objects.get(name="Credit Union")
cdfi = InstitutionType.objects.get(name="CDFI")
for row in filtered_usnic:
    if row["legal_name"] in existing_names:
        continue
    existing_names.add(row["legal_name"])
    # getting the datetime django wants
    naive_datetime = datetime.now()
    aware_datetime = timezone.make_aware(naive_datetime)
    new_name = row.get("legal_name") + "_FCU"
    rssd = row.get("rssd")
    # checks if rssd number is in the list and adds _CDFI
    if rssd in rssd_ids:
        new_name = row["legal_name"] + "_CDFI"
    # removes special characters except letters/numbers and spaces since we want to replace spaces with _
    tag_name = re.sub(r"[^A-Za-z0-9 ]+", "", row.get("legal_name").lower())
    mapped_rows = {
        "created": aware_datetime,
        "modified": aware_datetime,
        "ncua": row.get("ncua"),
        "countries": row.get("country"),
        "name": row.get("legal_name"),
        "aliases": new_name.lower(),
        "tag": generate_tag(tag_name.lower().replace(" ", "_"), 0, existing_tags),
        "rssd": rssd,
        "lei": row.get("lei"),
        "fdic_cert": row.get("fdic_cert"),
        "ein": row.get("ein"),
        "occ": row.get("occ"),
        "thrift_hc": row.get("thrift_hc"),
        "cusip": row.get("cusip"),
    }
    # adds tags to existing ones to check there are no duplicates
    existing_tags.add(mapped_rows["tag"])
    # checks if there is a website url and finds one if necessary
    website = row.get("website") or find_website(row.get("legal_name"))
    website = check_website_URL(website)
    mapped_rows["website"] = website
    # creates the Brand object
    brand = Brand.objects.create(**mapped_rows)
    commentary = Commentary.objects.create(display_on_website=True, brand=brand)
    if rssd in rssd_ids:
        commentary.institution_type.set([fcu, cdfi])
    else:
        commentary.institution_type.set([fcu])
    commentary.save()
    print(brand)
print("completed transfer of FCU")
