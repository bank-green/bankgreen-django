import os
import re
from datetime import datetime
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db.models import Q
from django.utils import timezone

import requests
from dotenv import load_dotenv

from brand.models import *
from brand.models.commentary import InstitutionType
from datasource.models import *


# to run in django shell using 'python manage.py shell'
# exec(open('scripts/groot_377/groot-377.py').read())


DIR = "scripts/groot_358/"
ENV_DIR = str(Path().cwd() / "bankgreen/.env")
load_dotenv(ENV_DIR)

australian_credit_unions = DIR + "australian_credit_unions.txt"


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


def check_website_URL(url):
    new_url = url.lower()
    validator = URLValidator()
    try:
        validator(new_url)
        return new_url
    except ValidationError:
        new_url = "https://" + new_url
        return new_url


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


print("starting groot-358.py")

australian_fcu = set()
number_of_entries = 0
regex_pattern = r"^(" + "|".join([re.escape(name) for name in australian_fcu]) + r")"
# gets information from a file that just have the values you are looking for
with open(australian_credit_unions, "r") as file:
    australian_fcu.update({line.strip() for line in file})
query = Q()
for name in australian_fcu:
    query |= Q(legal_name__iexact=name)
filtered_usnic = Usnic.objects.filter(query).values(
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
InstitutionType.objects.create(name="Credit Union", description="")
fcu = InstitutionType.objects.get(name="Credit Union")
for row in filtered_usnic:
    if row["legal_name"] in existing_names:
        continue
    existing_names.add(row["legal_name"])
    # getting the datetime django wants
    naive_datetime = datetime.now()
    aware_datetime = timezone.make_aware(naive_datetime)
    # removes special characters exept letters/numbers and spaces since we want to replace spaces with _
    tag_name = re.sub(r"[^A-Za-z0-9 ]+", "", row.get("legal_name").lower())
    mapped_rows = {
        "created": aware_datetime,
        "modified": aware_datetime,
        "ncua": row.get("ncua"),
        "countries": row.get("country"),
        "name": row.get("legal_name"),
        "aliases": row.get("legal_name").lower(),
        "tag": generate_tag(tag_name.lower().replace(" ", "_"), 0, existing_tags),
        "rssd": row.get("rssd"),
        "lei": row.get("lei"),
        "fdic_cert": row.get("fdic_cert"),
        "ein": row.get("ein"),
        "occ": row.get("occ"),
        "thrift_hc": row.get("thrift_hc"),
        "cusip": row.get("cusip"),
    }
    # adds tags to existing ones to check there are no duplicates
    existing_tags.add(mapped_rows["tag"])
    # checks if there is a website url
    websiteurl = row.get("website")
    if websiteurl != None:
        websiteurl = check_website_URL(websiteurl)
        mapped_rows["website"] = websiteurl
    Brand.objects.create(**mapped_rows)
    brand_instance = Brand.objects.get(name=mapped_rows["name"])
    commentary = Commentary.objects.create(display_on_website=True, brand=brand_instance)
    commentary.institution_type.set([fcu])
    commentary.save()
    number_of_entries += 1
print("completed transfer of CFU")