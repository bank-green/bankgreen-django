import re
from datetime import datetime

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand
from django.core.validators import URLValidator
from django.utils import timezone

from brand.models import *
from datasource.models import *


class Command(BaseCommand):
    help = "This script enters information from usnic into brands for FCU entity type"

    def handle(self, *args, **kwargs):
        print("Running db_changes_fcu.py")
        rssd_ids = []
        with open(r"datasource\management\commands\cdfi_rssd_numbers.txt", "r") as file:
            rssd_ids = [line.strip() for line in file]
        filtered_usnic = Usnic.objects.filter(entity_type="FCU").values(
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
        existing_tags = [x["tag"] for x in brand_values]
        existing_names = [["name"] for x in brand_values]
        for row in filtered_usnic:
            if row["legal_name"] in existing_names:
                continue
            else:
                existing_names.append(row["legal_name"])
            # getting the datetime django wants
            naive_datetime = datetime.now()
            aware_datetime = timezone.make_aware(naive_datetime)
            new_name = row["legal_name"] + "_FCU"
            try:
                rssd = row["rssd"]
                # checks if rssd number is in the list and adds _CDFI
                if rssd in rssd_ids:
                    new_name = row[3] + "_CDFI"
                    print("CDFI")
            except:
                rssd = ""
            # removes special characters exept letters/numbers and spaces since we want to replace spaces with _
            tag_name = re.sub(r"[^A-Za-z0-9 ]+", "", row["legal_name"].lower())
            mapped_rows = {
                "created": aware_datetime,
                "modified": aware_datetime,
                "ncua": row["ncua"],
                "countries": row["country"],
                "name": row["legal_name"],
                "aliases": new_name.lower(),
                "tag": _generate_tag(tag_name.lower().replace(" ", "_"), 0, existing_tags),
                "rssd": rssd,
                "lei": row["lei"],
                "fdic_cert": row["fdic_cert"],
                "ein": row["ein"],
                "occ": row["occ"],
                "thrift_hc": row["thrift_hc"],
                "cusip": row["cusip"],
            }
            # adds tags to existing ones to check there are no duplicates
            existing_tags.append(mapped_rows["tag"])
            # checks if there is a website url
            websiteurl = row["website"]
            if websiteurl != None:
                websiteurl = check_website_URL(row["website"].lower())
                mapped_rows["website"] = websiteurl
            # creates the Brand object
            Brand.objects.create(**mapped_rows)

        print("completed transfer of CFU")


def check_website_URL(url):
    if url == None:
        return ""
    else:
        validator = URLValidator()
        try:
            validator(url)
            return url
        except ValidationError:
            url = "https://" + url
            return url


def _generate_tag(bt_tag, increment=0, existing_tags=None):
    og_tag = bt_tag
    # memoize existing tags for faster recursion
    if increment < 1:
        bt_tag = og_tag
    else:
        bt_tag = og_tag + "_" + str(increment).zfill(2)

    if bt_tag not in existing_tags:
        return bt_tag
    else:
        return _generate_tag(og_tag, increment=increment + 1, existing_tags=existing_tags)
