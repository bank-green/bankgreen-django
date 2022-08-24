from django.db import models
from brand.models import Brand
from django_countries.fields import CountryField


class FeatureType(models.Model):
    name = models.CharField(
        max_length=40, help_text="i.e. Free Checking account, Credit Card, etc."
    )
    description = models.TextField(help_text="Description about this feature type")

    def __str__(self):
        return self.name


class FeatureAvailabilityChoice(models.TextChoices):
    YES = "Yes"
    NO = "No"
    MAYBE = "Maybe"
    NOT_APPLICABLE = "N/A"


class BrandFeature(models.Model):
    brand = models.ForeignKey(
        Brand, related_name="bank_features", null=False, blank=False, on_delete=models.CASCADE
    )

    feature = models.ForeignKey(FeatureType, null=False, blank=False, on_delete=models.CASCADE)

    offered = models.CharField(
        max_length=16,
        choices=FeatureAvailabilityChoice.choices,
        default=FeatureAvailabilityChoice.NOT_APPLICABLE,
        help_text="Is the feature offered?",
    )

    details = models.CharField(
        max_length=100, null=True, blank=True, help_text="Details about the feature"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["feature", "brand"], name="unique_feature_implementation_per_bank"
            )
        ]
