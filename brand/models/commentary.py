from enum import Enum

from django.db import models

from django_countries.fields import CountryField

from brand.models import Brand


class RatingChoice(models.TextChoices):
    GREAT = "great"
    OK = "ok"
    BAD = "bad"
    WORST = "worst"
    UNKNOWN = "unknown"


class Commentary(models.Model):
    # Metadata
    brand = models.OneToOneField(
        Brand,
        related_name="commentary",
        help_text="What brand is this comment associated with?",
        on_delete=models.CASCADE,
    )
    display_on_website = models.BooleanField(default=False)
    comment = models.TextField(help_text="Meta. Comments for staff and/or editors")
    rating = models.CharField(
        max_length=8,
        null=False,
        blank=False,
        choices=RatingChoice.choices,
        default=RatingChoice.UNKNOWN,
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
        max_length=200,
    )
    top_blurb_subheadline = models.CharField(
        help_text="Positive/Negative. i.e. According to the latest research*, in 2020 your bank was the 4th largest funder...",
        max_length=300,
    )

    # Negative Commentary
    snippet_1 = models.CharField(
        max_length=150,
        help_text="Negative. Custom fact about the brand. Used to fill in templates",
        blank=True,
        default="",
    )
    snippet_1_link = models.URLField(
        help_text="link to dirty deal 1 detauls", blank=True, default=""
    )
    snippet_2 = models.CharField(
        max_length=150,
        help_text="Negative. Custom fact about the brand. Used to fill in templates",
        blank=True,
        default="",
    )
    snippet_2_link = models.URLField(
        help_text="link to dirty deal 2 detauls", blank=True, default=""
    )
    snippet_3 = models.CharField(
        max_length=150,
        help_text="Negative. Custom fact about the brand. Used to fill in templates",
        blank=True,
        default="",
    )
    snippet_3_link = models.URLField(
        help_text="link to dirty deal 3 detauls", blank=True, default=""
    )

    # Positive Commentary
    top_three_ethical = models.BooleanField(
        help_text="Positive. Is this bank recommended best banks of a country page?", default=False
    )
    recommended_order = models.IntegerField(
        help_text="Positive. in case there are more recommended banks than can fit on the page, lower numbers are given priority",
        null=True,
        blank=True,
    )
    recommended_in = CountryField(
        multiple=True, help_text="Positive. what countries will this bank be recommended in?"
    )
    from_the_website = models.TextField(
        help_text="Positive. used to to describe green banks in their own words"
    )

    def __repr__(self):
        return f"Commentary: {self.brand.tag}"

    def __str__(self):
        return f"Commentary: {self.brand.tag}"
