from uuid import uuid4

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.views import PasswordResetView
from django.forms import inlineformset_factory
from django.forms.models import model_to_dict
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView
from django.core.exceptions import ObjectDoesNotExist

from cities_light.models import Region, SubRegion
from dal import autocomplete
from django.core import serializers

from .forms import BrandFeaturesForm, CreateUpdateForm
from .models import Brand, BrandFeature, BrandUpdate
from .models.commentary import InstitutionCredential, InstitutionType

import pathlib, csv, json, os
from datetime import datetime
from scripts.check_duplicates import return_all_duplicates
from scripts.find_missing_brands_vs_pages import (
    get_missing_brand_and_bankpages,
    get_missing_sfi_brands_and_pages,
    get_ref_id,
)
from utils.brand_utils import concat_brand_feature_data, get_institution_data


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


def serialize_brand_model_to_json():
    """
    serialize brand, commentary, brandfeature models
    save model into json format

    """

    results = []
    institute_dict = {}

    brand_instances = Brand.objects.select_related("commentary").all()
    instutute_type_data, instutute_credential_data = get_institution_data()

    for brand_instance in brand_instances:
        brand_serialized_data = serializers.serialize(
            "json", [brand_instance], use_natural_primary_keys=True, use_natural_foreign_keys=True
        )
        try:
            commentary_serialized_data = serializers.serialize(
                "json",
                [brand_instance.commentary],
                use_natural_primary_keys=True,
                use_natural_foreign_keys=True,
            )
        except ObjectDoesNotExist:
            pass

        brand_data = json.loads(brand_serialized_data)
        commentary_data = json.loads(commentary_serialized_data)

        feature_data = concat_brand_feature_data(brand_id=brand_data[0]["pk"])

        institute_dict["institution_type"] = ",".join([data.name for data in instutute_type_data])
        institute_dict["institution_credentials"] = ",".join(
            [data.name for data in instutute_credential_data]
        )

        brand_data[0]["fields"]["brand_id"] = brand_data[0]["pk"]
        brand_data[0]["fields"]["countries"] = ",".join(
            [country.name for country in brand_instance.countries]
        )
        brand_data[0]["fields"].update(commentary_data[0]["fields"])
        brand_data[0]["fields"].update(feature_data)
        brand_data[0]["fields"].update(institute_dict)
        brand_data[0]["fields"]["regions"] = ",".join(
            [
                reg_dict["display_name"]
                for reg_dict in brand_instance.regions.all().values("display_name")
            ]
        )
        brand_data[0]["fields"]["subregions"] = ",".join(
            [
                reg_dict["display_name"]
                for reg_dict in brand_instance.subregions.all().values("display_name")
            ]
        )
        results.append(json.loads(json.dumps(brand_data[0])))

    with open(r"data.json", "w") as file:
        json.dump(results, file)


def export_csv(request):
    """
    This function is used to export Brand related data into the csv file.
    """

    downloads_path = str(pathlib.Path.home() / "Downloads")
    csv_file_name = f"data_{datetime.now().strftime('%Y_%m_%d-%I_%M_%S_%p')}.csv"

    file_location = downloads_path + "/" + csv_file_name

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f"attachment;filename={csv_file_name}"

    serialize_brand_model_to_json()

    with open("data.json") as json_file:
        data = json.loads(json_file.read())

    # remove data.json file
    os.remove("data.json")

    # Create a CSV writer object
    csv_writer = csv.writer(response)

    # Write the header (column names)
    header = sorted(data[0]["fields"].keys())
    csv_writer.writerow(header)

    # Write the data rows
    for item in data:
        csv_writer.writerow(dict(sorted(item["fields"].items())).values())

    return response


def check_duplicates(request):
    suggested_duplicates = return_all_duplicates()
    return render(request, "button.html", context={"suggested_duplicates": suggested_duplicates})


def check_prismic_mismatches(request):
    """
    Return dict of mismatched brands, sfi brands, bankpages and sfipages
    """
    missing_brands_pages = {}
    ref = get_ref_id()

    missing_brands_pages.update(get_missing_brand_and_bankpages(ref))
    missing_brands_pages.update(get_missing_sfi_brands_and_pages(ref))

    return render(
        request,
        "missing_brand_vs_prismic_pages.html",
        context={"missing_brands_pages": missing_brands_pages},
    )


class CustomPasswordResetView(PasswordResetView):
    def form_valid(self, form):
        # Verifying if the email belong to registered user
        email = form.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            return super().form_valid(form)
        else:
            return render(self.request, "registration/email_not_found.html", {"email": email})
