from uuid import uuid4

from django.db import models

from model_utils.models import TimeStampedModel


class SwitchSurveyPlanning(TimeStampedModel):

    uuid = models.UUIDField(default=uuid4, editable=False, unique=True)

    email = models.EmailField()

    is_agree_privacy = models.BooleanField(default=False)
    is_agree_marketing = models.BooleanField(default=False)

    mailerlite_synced = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.email} ({self.uuid})"

    class Meta:
        ordering = ["-created"]
