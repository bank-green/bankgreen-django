from decimal import Decimal
from uuid import uuid4

from django.core.validators import MinValueValidator
from django.db import models

from django_countries.fields import CountryField
from model_utils.models import TimeStampedModel

from brand.models.brand import Brand


class SwitchSurveySubmission(TimeStampedModel):

    uuid = models.UUIDField(default=uuid4, editable=False, unique=True)

    class Currency(models.TextChoices):
        GBP = "GBP", "British Pound"
        USD = "USD", "US Dollar"
        EUR = "EUR", "Euro"
        CAD = "CAD", "Canadian Dollar"
        AUD = "AUD", "Australian Dollar"

    moved_from_bank_name = models.CharField(max_length=100)
    moved_from_brand = models.ForeignKey(
        Brand,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="switch_survey_moved_from",
    )

    moved_to_bank_name = models.CharField(max_length=100)
    moved_to_brand = models.ForeignKey(
        Brand,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="switch_survey_moved_to",
    )

    amount = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    currency = models.CharField(max_length=3, choices=Currency)

    country = CountryField(blank=True)
    region = models.CharField(max_length=100, blank=True)

    is_agree_privacy = models.BooleanField(default=False)
    is_agree_marketing = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.moved_from_bank_name} → {self.moved_to_bank_name} ({self.uuid})"

    class Meta:
        ordering = ["-created"]
        indexes = [models.Index(fields=["-created"])]
