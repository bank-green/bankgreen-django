import csv
import datetime
from datetime import timezone

from django.utils.timezone import make_aware

from brand.models.brand import Brand


"""
  to run:
  django shell < scripts/Groot_390/groot-390.py
"""


def enter_review_date(csvreader):
    tags_to_sync = []
    for idx, row in enumerate(csvreader):
        if idx == 0:
            continue

        tag = row[0]
        last_update = row[9]
        reviewed_date = row[13]
        rating_date = row[14]
        status = row[16]
        rater = row[6]

        date_to_use = reviewed_date or rating_date

        if not date_to_use and rater and status.lower() == "complete":
            date_to_use = last_update

        try:
            update_last_reviewed(tag, date_to_use)
            tags_to_sync.append(tag)
        except Exception as e:
            print(f"Failed on tag {tag}: {date_to_use} because of {e}")

        with open("synced_tags.txt", "w") as f:
            for tag in tags_to_sync:
                f.write(f"{tag}: {date_to_use}\n")

    print(len(tags_to_sync))


def update_last_reviewed(tag, last_reviewed):
    if last_reviewed.strip() == "":
        return

    last_reviewed = datetime.datetime.fromisoformat(last_reviewed)
    if not last_reviewed.tzinfo:
        last_reviewed = make_aware(last_reviewed, timezone.utc)

    brand = Brand.objects.get(tag=tag)
    commentary = brand.commentary
    commentary.last_reviewed = last_reviewed
    commentary.save()


with open("scripts/Groot_390/export.csv", newline="") as f:
    csvreader = csv.reader(f, delimiter=",")
    enter_review_date(csvreader)
