from django.db import models
from brand.models import Brand


class Features(models.Model):
    brand = models.OneToOneField(
        Brand,
        related_name="features",
        help_text="What brand is this comment associated with?",
        on_delete=models.CASCADE,
    )
    checking_saving = models.BooleanField(
        help_text="Positive. does the bank offer checkings or savings accounts?", default=False
    )
    checking_saving_details = models.CharField(
        help_text="Positive. Details on available checkings and savings accounts",
        max_length=100,
        blank=True,
        default="",
    )

    free_checking = models.BooleanField(
        help_text="Positive. does the bank offer free checkings?", default=False
    )
    free_checking_details = models.CharField(
        help_text="Positive. Details on available free checkings",
        max_length=100,
        blank=True,
        default="",
    )

    interest_rates = models.CharField(
        help_text="Positive. Details about offered interest rates",
        max_length=100,
        null=True,
        blank=True,
    )

    free_atm_withdrawal = models.BooleanField(
        help_text="Positive. does the bank offer free ATM withdrawals?", default=False
    )
    free_atm_withdrawal_details = models.CharField(
        help_text="Positive. Details on available free ATM withdrawals",
        max_length=100,
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
        help_text="Positive. Details on local branches", max_length=100, null=True, blank=True
    )

    mortgage_or_loan = models.BooleanField(
        help_text="Positive. does the bank offer mortgage or loans?", default=False
    )
    deposit_protection = models.CharField(
        help_text="Positive. Details on deposit protection", max_length=100, null=True, blank=True
    )

    credit_cards = models.BooleanField(
        help_text="Positive. does the bank offer credit cards?", default=False
    )
    credit_cards_details = models.CharField(
        help_text="Positive. Details on credit cards", max_length=100, null=True, blank=True
    )

    free_international_card_payment = models.BooleanField(
        help_text="Positive. does the bank offer free international card payments?", default=False
    )
    free_international_card_payment_details = models.CharField(
        help_text="Positive. Details on free international card payments",
        max_length=100,
        null=True,
        blank=True,
    )
