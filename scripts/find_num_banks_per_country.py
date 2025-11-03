"""script is meant to be copy-pasted into django shell.
In short, it prints the number of banks per country, with their ratings."""

from brand.models import Brand, Commentary, RatingChoice
from django.db.models import Count, F

from collections import OrderedDict
import yaml


# Step 1: Retrieve all unique country codes from brands that have commentaries.
# The 'countries' field (CountryField with multiple=True) stores country codes as a comma-separated string.
# We first fetch these strings, then split and collect unique codes in Python.
brands_with_commentaries_country_strings = (
    Brand.objects.filter(commentary__isnull=False).values_list("countries", flat=True).distinct()
)

all_unique_country_codes = set()
for country_string in brands_with_commentaries_country_strings:
    if country_string:  # Ensure the string is not empty
        # Split the comma-separated string into individual country codes
        for code in country_string.split(","):
            all_unique_country_codes.add(code.strip())  # Add cleaned codes to the set

# Initialize the dictionary to store the final results.
results_by_country = {}

# Step 2: For each identified unique country code, perform aggregations.
for country_code in all_unique_country_codes:
    # Filter for brands that operate in the current 'country_code' and have an associated commentary.
    # We use '__contains' to check if the country_code is part of the comma-separated string in the 'countries' field.
    brands_in_this_country_queryset = Brand.objects.filter(
        commentary__isnull=False, countries__contains=country_code
    )

    # Calculate the total number of unique banks (brands) in this specific country.
    # .distinct().count() ensures each brand is counted only once.
    total_banks_in_country = brands_in_this_country_queryset.distinct().count()

    # Aggregate the ratings for these banks within this country.
    # We annotate each brand with its commentary's rating, then group by rating and count distinct brands.
    ratings_summary_queryset = (
        brands_in_this_country_queryset.annotate(
            bank_rating=F("commentary__rating")  # Get the rating from the related Commentary
        )
        .values("bank_rating")  # Group by the bank's rating
        .annotate(count=Count("pk", distinct=True))  # Count unique brands for each rating group
        .order_by("bank_rating")  # Order for consistent output
    )

    # Convert the queryset of rating counts into a dictionary for easier access.
    # This also prepares for filling in any missing rating choices with a count of 0.
    ratings_counts_for_country = {
        item["bank_rating"]: item["count"] for item in ratings_summary_queryset
    }

    # Ensure all possible rating choices are present in the summary for completeness, initializing to 0 if not found.
    all_rating_choices = {choice.value for choice in RatingChoice}
    full_ratings_summary = {
        rating_choice: ratings_counts_for_country.get(rating_choice, 0)
        for rating_choice in all_rating_choices
    }

    # Store the compiled data for the current country.
    results_by_country[country_code] = {
        "total_banks": total_banks_in_country,
        "ratings": full_ratings_summary,
    }

filtered_results = {
    country_code: data
    for country_code, data in results_by_country.items()
    if data["total_banks"] > 10
}

sorted_filtered_results = dict(
    sorted(filtered_results.items(), key=lambda item: item[1]["total_banks"], reverse=True)
)

from brand.models.state import COUNTRIES  # Import the COUNTRIES dictionary

results_with_country_names = OrderedDict()
for country_code, data in sorted_filtered_results.items():
    country_name = COUNTRIES.get(
        country_code, country_code
    )  # Use country name, fallback to code if not found
    results_with_country_names[country_name] = data


# Print the sorted filtered results with country names in a YAML-like format
if results_with_country_names:
    print(yaml.dump(results_with_country_names, indent=2, sort_keys=False))
else:
    print("No countries found with more than 10 banks.")
