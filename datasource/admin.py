from django.contrib import admin

from .models import Banktrack


@admin.register(Banktrack)
class BanktrackAdmin(admin.ModelAdmin):
    # a list of displayed columns name.
    list_display = ["name", "website"]
    search_fields = ["name", "website"]
