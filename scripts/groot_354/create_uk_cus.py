import csv
import json
import os
import re
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator

import requests
from dotenv import load_dotenv

from brand.models import *
from brand.models.commentary import InstitutionType


ENV_DIR = str(Path().cwd() / "bankgreen/.env")
load_dotenv(ENV_DIR)

"""
This is a script to help us find credit unions that are already in DBG and go through them by hand

  to run:
  django shell < scripts/groot_354/create_uk_cus.py
"""


def normalize_name(name):
    """Normalize a name for better matching by removing common words and punctuation"""
    name = name.lower()
    name = re.sub(
        r"credit union|limited|ltd|association|cooperative|co-operative|society|savings", "", name
    )
    name = re.sub(r"[^a-z0-9]", " ", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name


def generate_tag(name):
    """Generate a tag from name"""
    tag = name.lower().replace(" ", "_")
    tag = re.sub(r"[^a-zA-Z0-9_]", "", tag)
    tag = tag.replace("__", "_")
    return tag


def is_url(string):
    validator = URLValidator()
    try:
        validator(string)
        return string
    except ValidationError:
        return None

    return string if pattern.match(string) else None


def find_website(cu_name):

    cache_file = "scripts/groot_354/website_cache.json"

    # Load cache if it exists
    if os.path.exists(cache_file):
        with open(cache_file, "r") as f:
            cache = json.load(f)
    else:
        cache = {}
    if cu_name in cache:
        return cache[cu_name]

    url = "https://api.perplexity.ai/chat/completions"

    payload = {
        "model": "sonar",
        "messages": [
            {"role": "system", "content": "return only a url."},
            {"role": "user", "content": f"Return this UK credit union's website {cu_name}"},
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
    website = json.loads(response.text)["choices"][0]["message"]["content"]
    valid_url = is_url(website)

    # Update cache
    if valid_url:
        cache[cu_name] = valid_url
        with open(cache_file, "w") as f:
            json.dump(cache, f)


with open("scripts/groot_354/uk_credit_unions.csv", newline="") as f:
    csvreader = csv.reader(f, delimiter="|")
    next(csvreader, None)
    cu_list = [x for x in csvreader]


existing_uk_cus = Brand.objects.filter(countries__contains="GB").filter(
    commentary__institution_type=InstitutionType.objects.get(name="Credit Union")
)


for row in cu_list:
    frn = row[1]
    new_name = row[2]
    tag = generate_tag(new_name)
    new_normalized_name = normalize_name(new_name)
    filtered_cus = existing_uk_cus.filter(name__contains=new_normalized_name)
    matching_tags = Brand.objects.filter(tag=tag)
    if len(filtered_cus) == 1:
        brand = filtered_cus[0]
        if not brand.website:
            brand.website = find_website(brand.name)
        brand.frn = cu_list[1]
        brand.commentary.display_on_website = True
        brand.save()
        brand.commentary.save()
    elif len(matching_tags) == 1:
        brand = matching_tags.first()
        if "GB" not in brand.countries:
            brand.countries.append("GB")
            brand.commentary.display_on_website = True
            brand.save()
            brand.commentary.save()
    elif len(filtered_cus) < 1 and len(matching_tags) < 1:
        website = find_website(new_name)
        print(new_name)
        breakpoint()
        try:
            new_brand, _ = Brand.objects.update_or_create(
                name=new_name, tag=tag, countries=["GB"], website=website
            )
            commentary = Commentary.objects.update_or_create(
                brand=new_brand, rating=RatingChoice.UNKNOWN, display_on_website=True
            )
        except Exception as e:
            breakpoint()
            print(f"{new_name}: Exception {e}\n---")
    else:
        print(f"brand not created: {new_name} | {tag}")
