from django.db import models
from django.core.validators import validate_email
from brand.models.brand import Brand
# from brand.models.commentary import Commentary


class Contact(models.Model):
    """
        This model serves as a repository for bank contacts
    """

    fullname = models.CharField(max_length=70)
    email = models.EmailField(validators=[validate_email], unique=True)
    # brand = models.ForeignKey('Brand', on_delete=models.CASCADE, related_name='contacts')
    brand_tag = models.CharField(max_length=250)
    brand_name = models.CharField(max_length=250)
    # b = models.ForeignKey(Commentary, on_delete=models.CASCADE, related_name="contacts", null=True, blank=True)
    # def save(self, *args, **kwargs):

    #     if not self.brand_tag:
    #         self.brand_tag = self.brand.tag
    #     if not self.brand_name:
    #         self.brand_name = self.brand.name

    #     super().save(*args, **kwargs)


    def __str__(self):
        return self.email