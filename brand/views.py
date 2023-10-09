from uuid import uuid4

from django.conf import settings
from django.forms import inlineformset_factory
from django.forms.models import model_to_dict
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView

from cities_light.models import Region, SubRegion
from dal import autocomplete

from .forms import BrandFeaturesForm, CreateUpdateForm
from .models import Brand, BrandFeature, BrandUpdate


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
    success_url = reverse_lazy("update_success")

    def form_valid(self, form):
        """
        If the form is valid, save the associated model.
        """
        brand_update = form.save(commit=False)
        context = self.get_context_data()
        brand_update.update_tag = context["tag"]
        brand_update.tag = context["tag"] + " (" + uuid4().hex + ")"
        brand_update.save()

        # proccess regions and subregions
        regions = self.request.POST.getlist("regions")
        for item in regions:
            reg = Region.objects.get(pk=item)
            brand_update.regions.add(reg)
        subregions = self.request.POST.getlist("subregions")
        for item in subregions:
            subreg = SubRegion.objects.get(pk=item)
            brand_update.subregions.add(subreg)

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


def update_success(request):
    template_name = "update_success.html"

    return render(request, template_name)


def brand_redirect(request, tag):
    try:
        brand_id = Brand.objects.get(tag=tag).pk
        admin_record_url = reverse("admin:brand_brand_change", args=[brand_id])
        return redirect(admin_record_url)
    except Brand.DoesNotExist:
        raise Http404(f"A brand with the tag {tag} was not found")


def calendar_redirect(request):
    return redirect(settings.SEMI_PUBLIC_CALENDAR_URL)
