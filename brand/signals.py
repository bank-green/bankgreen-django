from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.timezone import now

from .models import Commentary


@receiver(pre_save, sender=Commentary)
def update_last_reviewed(sender, instance, **kwargs):

    # Update last_reviewed for existing records.
 if instance.pk:
    instance.last_reviewed = now()