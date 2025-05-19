import json
import os
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator

import requests
from dotenv import load_dotenv

from brand.models import *
from brand.models.commentary import InstitutionType


"""
  script for finding and adding New Zealand credit unions. This was eventually done by hand
  but the script is here for reference.

  to run:
  django shell < scripts/groot_358/groot-359.py
"""

DIR = "scripts/groot_359/"
ENV_DIR = str(Path().cwd() / "bankgreen/.env")
load_dotenv(ENV_DIR)


brand_values = Brand.objects.values("tag", "name")
existing_tags = {x["tag"] for x in brand_values}
existing_names = {x["name"] for x in brand_values}
CU = InstitutionType.objects.get(name="Credit Union")


def generate_tag(desired_tag, existing_tags, increment=0):
    og_tag = desired_tag
    # memoize existing tags for faster recursion
    if increment < 1:
        desired_tag = og_tag
    else:
        desired_tag = og_tag + "_" + str(increment).zfill(2)

    if desired_tag not in existing_tags:
        return desired_tag
    else:
        return generate_tag(og_tag, increment=increment + 1, existing_tags=existing_tags)


def return_website_URL_or_none(url):

    validator = URLValidator()

    for prefix in ["", "https://"]:
        try:
            validator(url)
            return url.lower()
        except ValidationError:
            pass

        return None


def find_website(cu_name):
    url = "https://api.perplexity.ai/chat/completions"

    payload = {
        "model": "sonar",
        "messages": [
            {"role": "system", "content": "return only a url."},
            {
                "role": "user",
                "content": f"Return this New Zealand credit union's website {cu_name}",
            },
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
    return website


def create_credit_union(name):
    desired_tag = name.lower().strip().replace(" ", "_") + "_new_zealand"
    tag = generate_tag(desired_tag, existing_tags)
    website = return_website_URL_or_none(find_website(name))

    brand = Brand.objects.create(name=name, tag=tag, countries=["NZ"], website=website)
    commentary = Commentary.objects.create(display_on_website=True, brand=brand)
    commentary.institution_type.set([CU])
    commentary.save()
    brand.save()
    print(f"created {brand} with website {website}")


new_zealand_cus = []
with open(DIR + "new_zealand_cus.txt", "r") as file:
    new_zealand_cus = [line.strip() for line in file]

for name in new_zealand_cus:
    try:
        create_credit_union(name)
    except Exception as e:
        print(f"{name} EXCEPTION: {e}")
