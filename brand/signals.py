from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.timezone import now
from .models import Commentary

@receiver(pre_save, sender=Commentary)
def update_last_reviewed(sender, instance, **kwargs):
    """
    Update last_reviewed only if the rating has changed.
    """
    if instance.pk:  # Ensure it's an existing record
        try:
            old_instance = Commentary.objects.get(pk=instance.pk)
            if old_instance.rating != instance.rating:  # Only update if rating changed
                instance.last_reviewed = now()
        except Commentary.DoesNotExist:
            pass  # If no previous record exists, ignore
