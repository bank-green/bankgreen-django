from django.db import models


class EmbraceCampaign(models.Model):
    name = models.CharField(max_length=40)
    description = models.TextField()
    configuration = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.name
