import json
import time

from brand.models import Brand, Commentary, Contact
from brand.models.commentary import InstitutionType, RatingChoice


"""
to run from django shell:

exec(open('scripts/groot_357_import_ireland_credit_unions/iclu_to_brand.py').read())

"""
DIR = "scripts/groot_357_import_ireland_credit_unions/"
# !NOTE: get iclu.json from GROOT-357 ticket
IRISH_STANDARD_CREDIT_UNIONS = DIR + "iclu.json"
SUCCESS_TAGS_FILE = DIR + "success_tags.json"


def generate_tag(name):
    name = name.lower()
    name = name.replace(".", "")
    return name.replace(" ", "_")


def make_valid_website(url):
    if not url.startswith(("http://", "https://")):
        url = "http://" + url
    return url


COUNTRY_KEY = {"RepublicOfIreland": "IE", "NorthernIreland": "GB"}


print("Processing iclu...")
successful_tags = set()
failed = []

with open(SUCCESS_TAGS_FILE, "r") as open_file:
    already_saved_tags = json.load(open_file)["tags"]

with open(IRISH_STANDARD_CREDIT_UNIONS, "r") as open_file:
    json_result = json.load(open_file)

    # TODO: Double check "Credit Union" name
    credit_union_institution = InstitutionType.objects.get(name="Credit Union")
    for cu in json_result:
        try:
            countries = [COUNTRY_KEY[cu["country"]]]
            tag = generate_tag(name=cu["name"])

            # check if we've already ran script
            if tag in already_saved_tags:
                print(tag + " already saved, skipping...")
                continue

            website = make_valid_website(cu["website"])

            # Make Brand
            brand_instance = Brand(name=cu["name"], tag=tag, countries=countries, website=website)
            brand_instance.save()

            # Make Commentary
            commentary_instance = Commentary(
                brand=brand_instance, rating=RatingChoice.UNKNOWN, inherit_brand_rating=None
            )
            commentary_instance.save()

            # Add InstitutionType
            commentary_instance.institution_type.add(credit_union_institution)
            commentary_instance.save()

            # Make Contact for all subOffices
            for subOffice in cu["subOffice"]:
                contact_instance = Contact(
                    fullname=subOffice["name"],
                    email=subOffice["email"],
                    commentary=commentary_instance,
                )
                contact_instance.save()
            successful_tags.add(tag)
        except Exception as e:
            obj = {}
            obj["e"] = repr(e)
            if cu:
                obj["data"] = cu
            if tag:
                obj["tag"] = tag
            failed.append(obj)


print("Successful tags:: ", successful_tags)
print()
print("Number of successful: ", len(successful_tags))
print("Number of failed: ", len(failed))

# save a json list of successfull tags
with open(SUCCESS_TAGS_FILE, "w") as outfile:
    data = {}
    data["tags"] = list(successful_tags) + already_saved_tags
    json.dump(data, outfile, indent=2)

# save a json list of the failed attempts
timestamp = str(round(time.time()))
with open(DIR + f"failed_{timestamp}.json", "w") as outfile:
    json.dump(failed, outfile, indent=2)

print("Done")
