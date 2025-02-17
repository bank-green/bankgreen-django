from django.apps import AppConfig


class BrandConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "brand"

    def ready(self):
        import brand.signals
