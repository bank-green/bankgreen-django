from django.contrib import admin

from .models import Brand


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'tag', 'description']
    search_fields = ['name', 'tag', 'description']
