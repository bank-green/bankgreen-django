from brand.models.brand import Brand
from datetime import datetime
from django.db import models


class BrandSuggestion(Brand):
    """
        This is the extension of the Brand container with the additional parameters.
    """

    submitter_name = models.CharField(verbose_name="Name of the submitter", max_length=100, null=False,
                                      blank=False, default='unnamed')

    submitter_email = models.EmailField("Email of the submitter", max_length=100, blank=True)

    submission_date = models.DateTimeField(default=datetime.now, blank=True)

    brand_suggestion_id = models.BigAutoField(primary_key=True)

    class Meta:
        verbose_name_plural = "Brand suggestions"
