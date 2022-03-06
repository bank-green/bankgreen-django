from re import I
from tokenize import blank_re

from django.db import models

from django_countries.fields import CountryField

from brand.models import Brand


class Commentary(models.Model):
    # Metadata
    brand = models.ForeignKey(
        Brand,
        related_name="commentary_brand",
        help_text="What brand is this comment associated with?",
        null=False,
        blank=True,
        on_delete=models.CASCADE,
    )
    aliases = models.CharField(
        "Other names for the brand, comma seperated. i.e. BOFA, BOA",
        max_length=200,
        null=True,
        blank=True,
    )
    display_on_website = models.BooleanField(default=False)
    comment = models.TextField("Meta. Comments for staff and/or editors")
    rating = models.CharField("Rating", max_length=6, null=False, blank=False)

    # Neutral Commentary
    unique_statement = models.TextField(
        "Positive/Negative. i.e. Despite introducing policies to restrict unconventional oil and gas finance, BNP Paribas recently ",
        null=True,
        blank=True,
    )
    headline = models.CharField(
        "Positive/Negative. i.e. #1 in Coal", max_length=200, null=True, blank=True
    )

    top_blurb_headline = models.TextField(
        "Positive/Negative. i.e. Your money is being used to fund the climate crisis at an alarming rate."
    )
    top_blurb_subheadline = models.TextField(
        "Positive/Negative. i.e. According to the latest research*, in 2020 your bank was the 4th largest funder..."
    )

    # Negative Commentary
    snippet_1 = models.TextField(
        "Negative. Custom fact about the brand.",
        help_text="Used to fill in templates",
        blank=True,
        default="",
    )
    snippet_1_link = models.URLField("link to dirty deal 1 detauls", blank=True, default="")
    snippet_2 = models.TextField(
        "Negative. Custom fact about the brand.",
        help_text="Used to fill in templates",
        blank=True,
        default="",
    )
    snippet_2_link = models.URLField("link to dirty deal 2 detauls", blank=True, default="")
    snippet_3 = models.TextField(
        "Negative. Custom fact about the brand.",
        help_text="Used to fill in templates",
        blank=True,
        default="",
    )
    snippet_3_link = models.URLField("link to dirty deal 3 detauls", blank=True, default="")

    # Positive Commentary
    top_three_ethical = models.BooleanField(
        "Positive. Is this bank a top three bank?", default=False
    )
    recommended_order = models.IntegerField(
        "Positive. in case there are more recommended banks than can fit on the page, lower numbers are given priority",
        default=3,
        null=True,
    )
    recommended_in = CountryField(
        multiple=True, help_text="Positive. what countries will this bank be recommended in?"
    )
    from_the_website = models.TextField(
        "Positive. used to to describe green banks in their own words"
    )

    # Banking Detail Inforamtion, mostly used for recommended banks
    checking_saving = models.BooleanField(
        "Positive. does the bank offer checkings or savings accounts?", default=False
    )
    checking_saving_details = models.CharField(
        "Positive. Details on available checkings and savings accounts",
        max_length=100,
        blank=True,
        default="",
    )

    free_checking = models.BooleanField(
        "Positive. does the bank offer free checkings?", default=False
    )
    free_checking_details = models.CharField(
        "Positive. Details on available free checkings", max_length=100, blank=True, default=""
    )

    interest_rates = models.CharField(
        "Positive. Details about offered interest rates", max_length=100, null=True, blank=True
    )

    free_atm_withdrawl = models.BooleanField(
        "Positive. does the bank offer free ATM withdrawals?", default=False
    )
    free_atm_withdrawl_details = models.CharField(
        "Positive. Details on available free ATM withdrawals",
        max_length=100,
        blank=True,
        default="",
    )

    online_banking = models.BooleanField(
        "Positive. does the bank offer online banking?", default=False
    )
    local_branches = models.BooleanField(
        "Positive. does the bank offer local branches?", default=False
    )
    local_branches_custom = models.CharField(
        "Positive. Details on local branches", max_length=100, null=True, blank=True
    )

    mortgage_or_loan = models.BooleanField(
        "Positive. does the bank offer mortgage or loans?", default=False
    )
    deposit_protection = models.CharField(
        "Positive. Details on deposit protection", max_length=100, null=True, blank=True
    )

    credit_cards = models.BooleanField("Positive. does the bank offer credit cards?", default=False)
    credit_cards_details = models.CharField(
        "Positive. Details on credit cards", max_length=100, null=True, blank=True
    )

    free_international_card_payment = models.BooleanField(
        "Positive. does the bank offer free international card payments?", default=False
    )
    free_international_card_payment_details = models.CharField(
        "Positive. Details on free international card payments",
        max_length=100,
        null=True,
        blank=True,
    )
