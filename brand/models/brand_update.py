from brand.models.brand import Brand
from django.db import models


class BrandUpdate(Brand):
    """
    A "BrandUpdate" is container for updates to an existing Brand submitted by a user
    """

    UPDATE_FIELDS = ["name", "aliases", "website", "countries"]

    additional_info = models.TextField(
        "Add any additional information or explanation for this change",
        null=False,
        blank=True,
        default="",
    )

    update_tag = models.CharField(
        max_length=100,
        null=False,
        blank=False,
        editable=True,
        unique=False,
        help_text=("the tag we use or this brand record at Bank.Green. ",),
    )
