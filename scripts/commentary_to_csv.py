import csv

from brand.models import Commentary


cs = Commentary.objects.all()
# cs = [
#     x
#     for x in cs
#     if (
#         x.header.strip() != ""
#         or x.subtitle.strip() != ""
#         or x.summary.strip() != ""
#         or x.details.strip() != ""
#     )
# ]


csv_file = "commentaries.csv"

# Define the column names
fieldnames = [
    "brand_tag",
    "rating",
    "headline/header",
    "custom subtitle/subtitle",
    "description1/summary",
    "description2/details",
]

with open(csv_file, "w", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=";")
    writer.writeheader()
    for c in cs:
        writer.writerow(
            {
                "brand_tag": c.brand.tag,
                "rating": c.rating_inherited,
                "headline/header": c.headline,
                "custom subtitle/subtitle": c.subtitle,
                "description1/summary": c.description1,
                "description2/details": c.description2,
            }
        )

print(f"CSV file '{csv_file}' created successfully.")
