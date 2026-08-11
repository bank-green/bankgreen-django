from django.db import models

from model_utils.models import TimeStampedModel


class SwitchSurveyEmail(TimeStampedModel):

    submission = models.ForeignKey(
        "impact.SwitchSurveySubmission", on_delete=models.CASCADE, related_name="emails"
    )

    email = models.EmailField(unique=False)

    mailerlite_synced = models.BooleanField(default=False)

    def __str__(self):
        return self.email

    class Meta:
        verbose_name_plural = "Switch survey emails"
