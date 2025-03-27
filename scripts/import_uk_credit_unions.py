import json
import os
import re
import time
import django

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bankgreen.settings")
django.setup()

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils.text import slugify
from django.utils import timezone

from brand.models import Brand, Commentary
from brand.models.commentary import InstitutionType, RatingChoice

"""
To run from Django shell:

exec(open('scripts/groot_354_import_uk_credit_unions/import_uk_credit_unions.py').read())

"""

# Define paths
DIR = "scripts/groot_354_import_uk_credit_unions/"
UK_CREDIT_UNIONS_FILE = os.path.join(DIR + "uk_credit_unions.json")
SUCCESS_TAGS_FILE = DIR + "success_tags.json"


def generate_tag(name):
    """Generate a clean tag from the credit union name"""
    name = name.lower().replace(" ", "_")
    name = re.sub(r"[^a-zA-Z0-9_]", "", name)
    return name


print("Processing UK credit unions...")
successful_tags = set()
failed = []

# Load existing successfully saved brands
if os.path.exists(SUCCESS_TAGS_FILE):
    with open(SUCCESS_TAGS_FILE, "r") as open_file:
        already_saved_tags = json.load(open_file).get("tags", [])
else:
    already_saved_tags = []

# Load the UK credit unions list (assumed JSON format)
with open(UK_CREDIT_UNIONS_FILE, "r") as open_file:
    json_result = json.load(open_file)

# Get the "Credit Union" institution name
credit_union_institution = InstitutionType.objects.get(name="Credit Union")

for cu in json_result:
    try:
        firm_name = cu["Firm"].strip()
        frn = cu["FRN"].strip()

        tag = generate_tag(firm_name)

        # Check if we already processed this brand
        if tag in already_saved_tags:
            print(f"{tag} already saved, skipping...")
            continue

        # Look for an existing credit union
        existing_brand = Brand.objects.filter(name=firm_name).first()

        if existing_brand:
            # If the brand exists, update its Commentary to include FRN
            commentary, created = Commentary.objects.get_or_create(
                brand=existing_brand, defaults={"rating": RatingChoice.UNKNOWN, "FRN": frn}
            )
            if not created and not commentary.FRN:
                commentary.FRN = frn
                commentary.save()

            print(f"Updated existing credit union: {firm_name} with FRN: {frn}")
        else:
            # Create a new Brand
            new_brand = Brand.objects.create(name=firm_name, tag=tag)

            # Create associated Commentary
            commentary = Commentary.objects.create(
                brand=new_brand, rating=RatingChoice.UNKNOWN, FRN=frn
            )

            # Assign institution type
            commentary.institution_type.add(credit_union_institution)
            commentary.save()

            print(f"Created new credit union: {firm_name} with FRN: {frn}")

        successful_tags.add(tag)

    except ValidationError as e:
        failed.append({"error": repr(e), "data": cu, "tag": tag})
    except IntegrityError:
        # Integrity errors are likely from duplicate emails in contacts.
        pass

print("Successful tags:: ", successful_tags)
print("Number of successful: ", len(successful_tags))
print("Number of failed: ", len(failed))

# Save a JSON list of successfully processed brands
with open(SUCCESS_TAGS_FILE, "w") as outfile:
    json.dump({"tags": list(successful_tags) + already_saved_tags}, outfile, indent=2)

# Save a JSON list of failed imports (for debugging)
timestamp = str(round(time.time()))
with open(DIR + f"failed_{timestamp}.json", "w") as outfile:
    json.dump(failed, outfile, indent=2)

print("Done processing UK credit unions.")
