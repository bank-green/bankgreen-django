from enum import Enum

from django.core.validators import MinValueValidator
from django.db import models

from django_countries.fields import CountryField

from brand.models import Brand


class RatingChoice(models.TextChoices):
    GREAT = "great"
    OK = "ok"
    BAD = "bad"
    WORST = "worst"
    UNKNOWN = "unknown"


class ResultPageVariationChoice(models.TextChoices):
    RAN = "ran"
    BIMPACT = "bimpact"
    FAIRFINANCE = "fairfinance"
    GABV = "gabv"
    BLANK = ""


class Commentary(models.Model):
    # Metadata
    brand = models.OneToOneField(
        Brand,
        related_name="commentary",
        help_text="What brand is this comment associated with?",
        on_delete=models.CASCADE,
    )
    display_on_website = models.BooleanField(default=False)
    number_of_requests = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    comment = models.TextField(help_text="Meta. Comments for staff and/or editors", blank=True)
    rating = models.CharField(
        max_length=8,
        null=False,
        blank=False,
        choices=RatingChoice.choices,
        default=RatingChoice.UNKNOWN,
    )
    fossil_free_alliance = models.BooleanField(
        default=False, help_text="Is this brand in the fossil free alliance?"
    )

    # Neutral Commentary
    unique_statement = models.CharField(
        help_text="Positive/Negative. i.e. Despite introducing policies to restrict unconventional oil and gas finance, BNP Paribas recently ",
        null=True,
        max_length=300,
        blank=True,
    )
    headline = models.CharField(
        help_text="Positive/Negative. i.e. #1 in Coal", max_length=200, null=True, blank=True
    )

    top_blurb_headline = models.CharField(
        help_text="Positive/Negative. i.e. Your money is being used to fund the climate crisis at an alarming rate.",
        max_length=300,
        blank=True,
    )
    top_blurb_subheadline = models.CharField(
        help_text="Positive/Negative. i.e. According to the latest research*, in 2020 your bank was the 4th largest funder...",
        max_length=500,
        blank=True,
    )

    # Negative Commentary
    snippet_1 = models.CharField(
        max_length=300,
        help_text="Negative. Custom fact about the brand. Used to fill in templates",
        blank=True,
        default="",
    )
    snippet_1_link = models.URLField(
        help_text="link to dirty deal 1 detauls", blank=True, default=""
    )
    snippet_2 = models.CharField(
        max_length=300,
        help_text="Negative. Custom fact about the brand. Used to fill in templates",
        blank=True,
        default="",
    )
    snippet_2_link = models.URLField(
        help_text="link to dirty deal 2 detauls", blank=True, default=""
    )
    snippet_3 = models.CharField(
        max_length=300,
        help_text="Negative. Custom fact about the brand. Used to fill in templates",
        blank=True,
        default="",
    )
    snippet_3_link = models.URLField(
        help_text="link to dirty deal 3 detauls", blank=True, default=""
    )

    amount_financed_since_2016 = models.CharField(
        max_length=150,
        help_text="Negative. Amount of fossil fuel investment the brand has financed since the paris accord, i.e. $382 billion USD",
        blank=True,
        null=True,
        default=None,
    )

    # Positive Commentary
    top_three_ethical = models.BooleanField(
        help_text="Positive. Is this bank recommended best banks of a country page?", default=False
    )
    recommended_in = CountryField(
        multiple=True,
        help_text="Positive. what countries will this bank be recommended in?",
        blank=True,
    )
    from_the_website = models.TextField(
        help_text="Positive. used to to describe green banks in their own words", blank=True
    )

    our_take = models.TextField(
        help_text="Positive. used to to give our take on green banks", blank=True
    )
    result_page_variation = models.CharField(
        max_length=20,
        help_text="Used to customize how we display the brand result page on the frontend",
        blank=True,
        choices=ResultPageVariationChoice.choices,
        default=ResultPageVariationChoice.BLANK,
    )

    certified_fossil_free = models.BooleanField(
        help_text="Is this bank part of the Fossil Free Alliance?", default=False
    )

    def __repr__(self):
        return f"Commentary: {self.brand.tag}"

    def __str__(self):
        return f"Commentary: {self.brand.tag}"
