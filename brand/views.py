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

import pathlib, pycountry, csv
from datetime import datetime


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


def country_code_to_country_name(data):

    return (
        pycountry.countries.get(alpha_3=data).name
        if len(data) == 3
        else pycountry.countries.get(alpha_2=data).name
    )


def get_brand_data():
    """
    Retrieve all Brand data from the database.
    """
    return Brand.objects.all()


def get_institution_data():
    """
    Retrieve all Institute data from the database.
    """
    return InstitutionType.objects.all(), InstitutionCredential.objects.all()


def concat_brand_feature_data(brand_id):
    """
    Return concateneted brand feature data fieldwise.
    """
    data_dict = {}

    brand_feature_data = BrandFeature.objects.filter(brand_id=brand_id)

    if brand_feature_data:
        data_dict["brand feature id"] = ",".join([str(x.id) for x in brand_feature_data])
        data_dict["feature"] = ",".join([str(x.feature) for x in brand_feature_data])

    return data_dict


def concat_commentary_data(brand_id):
    """
    Return concateneted commentary data fieldwise.
    """
    data_dict = {}

    commentary_data = Commentary.objects.filter(brand_id=brand_id)

    if commentary_data:
        data_dict["commentary id"] = ",".join([str(c_data.id) for c_data in commentary_data])
        data_dict["inherit_brand_rating"] = ",".join(
            [str(c_data.inherit_brand_rating) for c_data in commentary_data]
        )
        data_dict["display_on_website"] = ",".join(
            [str(c_data.display_on_website) for c_data in commentary_data]
        )
        data_dict["number_of_requests"] = ",".join(
            [str(c_data.number_of_requests) for c_data in commentary_data]
        )
        data_dict["comment"] = ",".join([c_data.comment for c_data in commentary_data])
        data_dict["rating"] = ",".join([c_data.rating for c_data in commentary_data])
        data_dict["top_pick"] = ",".join([str(c_data.top_pick) for c_data in commentary_data])
        data_dict["semiautomatic_harassment"] = ",".join(
            [c_data.semiautomatic_harassment for c_data in commentary_data]
        )
        data_dict["fossil_free_alliance"] = ",".join(
            [str(c_data.fossil_free_alliance) for c_data in commentary_data]
        )
        data_dict["fossil_free_alliance_rating"] = ",".join(
            [str(c_data.fossil_free_alliance_rating) for c_data in commentary_data]
        )
        data_dict["show_on_sustainable_banks_page"] = ",".join(
            [str(c_data.show_on_sustainable_banks_page) for c_data in commentary_data]
        )
        data_dict["from_the_website"] = ",".join(
            [str(c_data.from_the_website) for c_data in commentary_data]
        )
        data_dict["subtitle"] = ",".join([str(c_data.subtitle) for c_data in commentary_data])
        data_dict["header"] = ",".join([str(c_data.header) for c_data in commentary_data])
        data_dict["summary"] = ",".join([c_data.summary for c_data in commentary_data])
        data_dict["details"] = ",".join([c_data.details for c_data in commentary_data])

    return data_dict


def export_csv(request):
    """
    This function is used to export Brand related data into the csv file.
    """

    # csv file path
    csv_file_name = f"brand_export_{datetime.now().strftime('%Y_%m_%d-%I_%M_%S_%p')}.csv"
    csv_file_path = str(pathlib.Path.home() / "Downloads") + f"/{csv_file_name}"

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f"attachment; filename={csv_file_name}"

    # headers of the csv file
    fieldnames = [
        "brand id",
        "commentary id",
        "brand feature id",
        "created",
        "modified",
        "name",
        "name_locked",
        "aliases",
        "description",
        "description_locked",
        "website",
        "website_locked",
        "countries",
        "tag",
        "tag_locked",
        "permid",
        "isin",
        "viafid",
        "lei",
        "googleid",
        "rssd",
        "rssd_hd",
        "cusip",
        "thrift",
        "thrift_hc",
        "aba_prim",
        "ncua",
        "fdic_cert",
        "occ",
        "ein",
        "regions",
        "subregions",
        "inherit_brand_rating",
        "display_on_website",
        "number_of_requests",
        "comment",
        "rating",
        "top_pick",
        "semiautomatic_harassment",
        "fossil_free_alliance",
        "fossil_free_alliance_rating",
        "amount_financed_since_2016",
        "show_on_sustainable_banks_page",
        "from_the_website",
        "our_take",
        "subtitle",
        "header",
        "summary",
        "details",
        "institution_type",
        "institution_credentials",
        "feature",
    ]

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

        data_dict["brand id"] = b_data.id
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

        brand_obj = Brand.objects.get(pk=data_dict["brand id"])

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

        commentary_data = concat_commentary_data(brand_id=data_dict["brand id"])
        brand_feature_data = concat_brand_feature_data(brand_id=data_dict["brand id"])

        data_dict.update(commentary_data)
        data_dict.update(brand_feature_data)

        writer.writerow(data_dict)

    return response
