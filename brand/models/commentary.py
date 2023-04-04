from enum import Enum

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from django_countries.fields import CountryField

from brand.models import Brand


class RatingChoice(models.TextChoices):
    GREAT = "great"
    OK = "ok"
    BAD = "bad"
    WORST = "worst"
    UNKNOWN = "unknown"
    INHERIT = "inherit"


class Commentary(models.Model):
    # Metadata
    brand = models.OneToOneField(
        Brand,
        related_name="commentary",
        help_text="What brand is this comment associated with?",
        on_delete=models.CASCADE,
    )

    inherit_brand_rating = models.ForeignKey(
        Brand,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inherit_brand_rating",
        help_text="should this brand have a rating inherited from another? If so, save will override the existing rating using the parent's rating unless the parent rating is blank.",
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

    @property
    def rating_inherited(self):
        return self.compute_inherited_rating()

    def compute_inherited_rating(self, inheritance_set=None, throw_error=False):

        inheritance_set = set() if inheritance_set is None else inheritance_set
        brand_in_inheritance_set = self.brand in inheritance_set

        if throw_error and brand_in_inheritance_set:
            raise ValidationError(
                "Commentary rating is inherited from itself. Please assign a non-inherited rating."
            )
        elif not throw_error and brand_in_inheritance_set:
            return RatingChoice.UNKNOWN
        elif self.rating == RatingChoice.INHERIT and not self.inherit_brand_rating:
            return RatingChoice.UNKNOWN
        elif self.rating == RatingChoice.INHERIT and self.inherit_brand_rating:
            inheritance_set.add(self.brand)
            return self.inherit_brand_rating.commentary.compute_inherited_rating(
                inheritance_set, throw_error=throw_error
            )

        return self.rating

    fossil_free_alliance = models.BooleanField(
        default=False, help_text="Is this brand in the fossil free alliance?"
    )

    fossil_free_alliance_rating = models.IntegerField(
        blank=False,
        null=False,
        default=-1,
        help_text="the fossil free alliance rating. Values between -1 and 5. 0 for unknown rating. -1 for not FFA",
        validators=[MinValueValidator(-1), MaxValueValidator(5)],
    )

    # Neutral Commentary
    # Deprecated. DO NOT USE. Will be deleted later.
    unique_statement = models.CharField(
        help_text="Positive/Negative. i.e. Despite introducing policies to restrict unconventional oil and gas finance, BNP Paribas recently ",
        null=True,
        max_length=300,
        blank=True,
    )

    # Deprecated. DO NOT USE. Will be deleted later.
    headline = models.CharField(
        help_text="Positive/Negative. i.e. #1 in Coal", max_length=200, null=True, blank=True
    )

    # Deprecated. DO NOT USE. Will be deleted later.
    top_blurb_headline = models.CharField(
        help_text="Positive/Negative. i.e. Your money is being used to fund the climate crisis at an alarming rate.",
        max_length=300,
        blank=True,
    )
    # Deprecated. DO NOT USE. Will be deleted later.
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

    # Deprecated. DO NOT USE. Will be deleted later.
    amount_financed_since_2016 = models.CharField(
        max_length=150,
        help_text="Negative. Amount of fossil fuel investment the brand has financed since the paris accord, i.e. $382 billion USD",
        blank=True,
        null=True,
        default=None,
    )

    # Positive Commentary

    # Deprecated. DO NOT USE. Will be deleted later.
    top_three_ethical = models.BooleanField(
        help_text="Positive. Is this bank recommended best banks of a country page?", default=False
    )
    # Deprecated. DO NOT USE. Will be deleted later.
    recommended_in = CountryField(
        multiple=True,
        help_text="Positive. what countries will this bank be recommended in?",
        blank=True,
    )
    show_on_sustainable_banks_page = models.BooleanField(
        help_text="Positive. Check if bank should be shown on sustainable banks page.",
        default=False,
    )
    from_the_website = models.TextField(
        help_text="Positive. used to to describe green banks in their own words", blank=True
    )

    our_take = models.TextField(
        help_text="Positive. used to to give our take on green banks", blank=True
    )

    subtitle = models.TextField(
        help_text="Markdown. Displayed immediately under the bank name", blank=True
    )

    header = models.TextField(
        help_text="Markdown. Displayed as the header to the summary on the first page of a bank's site.",
        blank=True,
    )
    summary = models.TextField(
        help_text="Markdown. Displayed as the first overview text on a bank's site.", blank=True
    )

    details = models.TextField(
        help_text="Markdown. Displayed as the overview of a bank's activities once you scroll down to their second page.",
        blank=True,
    )

    def __repr__(self):
        return f"Commentary: {self.brand.tag}"

    def __str__(self):
        return f"Commentary: {self.brand.tag}"

    def clean(self):
        # Ensure no cycles when saving
        _ = self.compute_inherited_rating(throw_error=True)

    def save(self, *args, **kwargs):
        if self.inherit_brand_rating:
            self.rating = RatingChoice.INHERIT

        if self.fossil_free_alliance and self.fossil_free_alliance_rating < 0:
            self.fossil_free_alliance_rating = 0
        elif not self.fossil_free_alliance:
            self.fossil_free_alliance_rating = -1
