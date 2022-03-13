from enum import Enum

from django.db import models

from django_countries.fields import CountryField

from brand.models import Brand


class RatingChoice(Enum):
    GREAT = "great"
    OK = "ok"
    BAD = "bad"
    WORST = "worst"
    UNKNOWN = "unknown"


class Commentary(models.Model):
    # Metadata
    brand = models.OneToOneField(
        Brand,
        related_name="commentary_brand",
        help_text="What brand is this comment associated with?",
        on_delete=models.CASCADE,
    )
    aliases = models.CharField(
        help_text="Other names for the brand, used for search. comma seperated. i.e. BOFA, BOA",
        max_length=200,
        null=True,
        blank=True,
    )
    display_on_website = models.BooleanField(default=False)
    comment = models.TextField(help_text="Meta. Comments for staff and/or editors")
    rating = models.CharField(
        max_length=8, null=False, blank=False, choices=[(tag, tag.value) for tag in RatingChoice]
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

    # Banking Detail Inforamtion, mostly used for recommended banks
    checking_saving = models.BooleanField(
        help_text="Positive. does the bank offer checkings or savings accounts?", default=False
    )
    checking_saving_details = models.CharField(
        help_text="Positive. Details on available checkings and savings accounts",
        max_length=50,
        blank=True,
        default="",
    )

    free_checking = models.BooleanField(
        help_text="Positive. does the bank offer free checkings?", default=False
    )
    free_checking_details = models.CharField(
        help_text="Positive. Details on available free checkings",
        max_length=50,
        blank=True,
        default="",
    )

    interest_rates = models.CharField(
        help_text="Positive. Details about offered interest rates",
        max_length=50,
        null=True,
        blank=True,
    )

    free_atm_withdrawl = models.BooleanField(
        help_text="Positive. does the bank offer free ATM withdrawals?", default=False
    )
    free_atm_withdrawl_details = models.CharField(
        help_text="Positive. Details on available free ATM withdrawals",
        max_length=50,
        blank=True,
        default="",
    )

    online_banking = models.BooleanField(
        help_text="Positive. does the bank offer online banking?", default=False
    )
    local_branches = models.BooleanField(
        help_text="Positive. does the bank offer local branches?", default=False
    )
    local_branches_details = models.CharField(
        help_text="Positive. Details on local branches", max_length=50, null=True, blank=True
    )

    mortgage_or_loan = models.BooleanField(
        help_text="Positive. does the bank offer mortgage or loans?", default=False
    )
    deposit_protection = models.CharField(
        help_text="Positive. Details on deposit protection", max_length=50, null=True, blank=True
    )

    credit_cards = models.BooleanField(
        help_text="Positive. does the bank offer credit cards?", default=False
    )
    credit_cards_details = models.CharField(
        help_text="Positive. Details on credit cards", max_length=50, null=True, blank=True
    )

    free_international_card_payment = models.BooleanField(
        help_text="Positive. does the bank offer free international card payments?", default=False
    )
    free_international_card_payment_details = models.CharField(
        help_text="Positive. Details on free international card payments",
        max_length=50,
        null=True,
        blank=True,
    )

    def __repr__(self):
        return f"Commentary: {self.brand.tag}"

    def __str__(self):
        return f"Commentary: {self.brand.tag}"
