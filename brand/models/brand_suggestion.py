from datetime import datetime
from django.db import models
from .brand import Brand


class BrandSuggestion(Brand):
    """
    This is the extension of the Brand container with the additional parameters.
    """

    submitter_name = models.CharField(
        verbose_name="Name of the submitter",
        max_length=100,
        null=False,
        blank=False,
        default="unnamed",
    )

    submitter_email = models.EmailField("Email of the submitter", max_length=100, blank=True)

    submission_date = models.DateTimeField(default=datetime.now, blank=True)

    class Meta:
        verbose_name_plural = "Brand suggestions"
