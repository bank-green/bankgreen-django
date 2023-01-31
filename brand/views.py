from unicodedata import name
from uuid import uuid4
from dal import autocomplete

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.views.generic import CreateView
from django.forms.models import model_to_dict
from django.forms import (
    ModelForm,
    ModelMultipleChoiceField,
    inlineformset_factory,
    ModelChoiceField,
    Form,
)

from brand.models import brand
from .models import Brand, BrandUpdate, BrandFeature
from .forms import CreateUpdateForm, BrandFeaturesForm

from cities_light.models import Region, SubRegion


class RegionAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated:
            return Region.objects.all()

        qs = Region.objects.all()

        if self.q:
            qs = qs.filter(name__icontains=self.q)

        return qs


class SubRegionAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated:
            return SubRegion.objects.all()

        qs = SubRegion.objects.all()

        if self.q:
            qs = qs.filter(name__icontains=self.q)

        return qs



class CreateUpdateView(CreateView):
    template_name = "update.html"
    form_class = CreateUpdateForm
    success_url = "https://bank.green"

    def form_valid(self, form):
        """
        If the form is valid, save the associated model.
        """
        print(self.request.POST)
        brand_update = form.save(commit=False)
        context = self.get_context_data()
        brand_update.update_tag = context["tag"]
        brand_update.tag = context["tag"] + " (" + uuid4().hex + ")"
        brand_update.save()
        print(brand_update.regions)
        print(brand_update.subregions)
        features = context["features"]
        features.instance = brand_update
        features.save()
        return redirect(self.success_url)

    def get_initial(self):
        if hasattr(self, "original"):  # ugly af
            return model_to_dict(self.original)

    def get_context_data(self, **kwargs):

        # set tag
        tag = self.kwargs.get("tag")
        original = Brand.objects.get(tag=tag)
        self.original = original

        context = super(CreateUpdateView, self).get_context_data(**kwargs)

        # set features
        initial = [
            model_to_dict(feature, fields=["offered", "details", "feature"])
            for feature in self.original.bank_features.all()
        ]
        BrandFeaturesFormSet = inlineformset_factory(
            BrandUpdate,
            BrandFeature,
            form=BrandFeaturesForm,
            extra=len(initial) + 3,
            can_delete=False,
        )

        if self.request.POST:
            context["features"] = BrandFeaturesFormSet(self.request.POST)
        else:
            context["features"] = BrandFeaturesFormSet(initial=initial)
        context["tag"] = tag
        return context


