from django.db import models
from django.core.validators import validate_email
from brand.models.brand import Brand
from brand.models.commentary import Commentary


class Contact(models.Model):
    """
    This model serves as a repository for bank contacts
    """

    fullname = models.CharField(max_length=70)
    email = models.EmailField(validators=[validate_email], unique=True)
    commentary = models.ForeignKey(Commentary, on_delete=models.CASCADE, null=True, blank=True)

    @property
    def brand_tag(self):
        if self.commentary:
            return self.commentary.brand.tag
        return None

    @property
    def brand_name(self):
        if self.commentary:
            return self.commentary.brand.name
        return None

    def __str__(self):
        return self.email
