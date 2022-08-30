from unicodedata import name
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.views import generic

from .models import Brand, BrandUpdate


class CreateUpdateView(generic.CreateView):
    template_name = "update.html"
    model = BrandUpdate
    fields = ["name", "description"]
