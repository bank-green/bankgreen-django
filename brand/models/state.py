from django.db import models


COUNTRIES = {"US": "United States", "CA": "Canada", "AU": "Australia"}


class State(models.Model):
    tag = models.CharField(max_length=100, primary_key=True, null=False, blank=False)
    name = models.CharField(max_length=100, null=False, blank=False)

    """
    Country code of Bank.Green supported country states
    Must be compatable with django_countries `code` (ISO 3166-1 code 2)
    """

    class CountryCode(models.TextChoices):
        US = "US"
        CA = "CA"
        AU = "AU"

    country_code = models.CharField(max_length=2, choices=CountryCode.choices)

    def __str__(self):
        return f"{self.name}, {COUNTRIES[self.country_code]}"
