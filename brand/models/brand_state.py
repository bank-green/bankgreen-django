from django.core.exceptions import ValidationError
from django.db import models

from brand.models.state import State

from .brand import Brand


class StateBaseModel(models.Model):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
    state = models.ForeignKey(State, on_delete=models.CASCADE)

    class Meta:
        abstract = True

    def clean(self):
        valid_country = False
        for c in self.brand.countries:
            if c.code == self.state.country_code:
                valid_country = True
        if not valid_country:
            raise ValidationError("Cannot create, State is not in any of the Brand's Countries")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.brand.tag}: {self.brand.pk}, {self.state.tag}: {self.state.pk}"


class StateLicensed(StateBaseModel):
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["brand", "state"], name="unique_brand_state_licensed")
        ]


class StatePhysicalBranch(StateBaseModel):
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["brand", "state"], name="unique_brand_state_physical")
        ]
