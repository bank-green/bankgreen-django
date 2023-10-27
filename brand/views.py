from uuid import uuid4

from django.conf import settings
from django.forms import inlineformset_factory
from django.forms.models import model_to_dict
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView

from cities_light.models import Region, SubRegion
from dal import autocomplete

from .forms import BrandFeaturesForm, CreateUpdateForm
from .models import Brand, BrandFeature, BrandUpdate, Commentary
from .models.commentary import InstitutionCredential, InstitutionType

import pathlib, csv
from datetime import datetime
from scripts.check_duplicates import return_all_duplicates
from utils.brand_utils import (
    concat_commentary_data,
    concat_brand_feature_data,
    get_brand_data,
    get_institution_data,
)


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


def export_csv(request):
    """
    This function is used to export Brand related data into the csv file.
    """

    # csv file name
    csv_file_name = f"brand_export_{datetime.now().strftime('%Y_%m_%d-%I_%M_%S_%p')}.csv"

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f"attachment; filename={csv_file_name}"

    # headers of the csv file
    brand_fields = [field.name for field in Brand._meta.get_fields()][10:]

    commentary_fields = [field.name for field in Commentary._meta.get_fields()][2:]
    commentary_fields[0] = "inherit_brand_rating_id"

    fieldnames = ["brand_id", "commentary_id", "brand_feature_id"]
    fieldnames.extend(brand_fields)
    fieldnames.extend(commentary_fields)
    fieldnames.append("feature")

    # reading model(Brand, InstitutionType and InstitutionCredential) data
    brand_all_data = get_brand_data()
    instutute_type_data, instutute_credential_data = get_institution_data()

    writer = csv.DictWriter(response, fieldnames=fieldnames, delimiter=";")
    writer.writeheader()

    for b_data in brand_all_data:
        data_dict = {}

        data_dict["institution_type"] = ",".join([data.name for data in instutute_type_data])
        data_dict["institution_credentials"] = ",".join(
            [data.name for data in instutute_credential_data]
        )

        data_dict["brand_id"] = b_data.id
        data_dict["created"] = b_data.created
        data_dict["modified"] = b_data.modified
        data_dict["name"] = b_data.name
        data_dict["name_locked"] = b_data.name_locked
        data_dict["aliases"] = b_data.aliases
        data_dict["description"] = b_data.description
        data_dict["description_locked"] = b_data.description_locked
        data_dict["website"] = b_data.website
        data_dict["website_locked"] = b_data.website_locked
        data_dict["countries"] = ",".join([country.name for country in b_data.countries])
        data_dict["tag"] = b_data.tag
        data_dict["tag_locked"] = b_data.tag_locked
        data_dict["permid"] = b_data.permid
        data_dict["isin"] = b_data.isin
        data_dict["viafid"] = b_data.viafid
        data_dict["lei"] = b_data.lei
        data_dict["googleid"] = b_data.googleid
        data_dict["rssd"] = b_data.rssd
        data_dict["rssd_hd"] = b_data.rssd_hd
        data_dict["cusip"] = b_data.cusip
        data_dict["thrift"] = b_data.thrift
        data_dict["aba_prim"] = b_data.aba_prim
        data_dict["ncua"] = b_data.ncua
        data_dict["fdic_cert"] = b_data.fdic_cert
        data_dict["occ"] = b_data.occ
        data_dict["ein"] = b_data.ein

        brand_obj = Brand.objects.get(pk=data_dict["brand_id"])

        concat_regions = ",".join(
            [
                reg_dict["display_name"]
                for reg_dict in brand_obj.regions.all().values("display_name")
            ]
        )
        data_dict["regions"] = concat_regions

        concat_subregions = ",".join(
            [
                reg_dict["display_name"]
                for reg_dict in brand_obj.subregions.all().values("display_name")
            ]
        )
        data_dict["subregions"] = concat_subregions

        commentary_data = concat_commentary_data(brand_id=data_dict["brand_id"])
        brand_feature_data = concat_brand_feature_data(brand_id=data_dict["brand_id"])

        data_dict.update(commentary_data)
        data_dict.update(brand_feature_data)

        writer.writerow(data_dict)

    return response


def check_duplicates(request):
    suggested_duplicates = return_all_duplicates()
    return render(request, "button.html", context={"suggested_duplicates": suggested_duplicates})
