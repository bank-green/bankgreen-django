from datetime import timedelta

from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import redirect
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html

from django_admin_listfilter_dropdown.filters import ChoiceDropdownFilter
from reversion.admin import VersionAdmin

from brand.admin_utils import link_contacts
from brand.forms import EmbraceCampaignForm
from brand.models import State
from brand.models.brand_suggestion import BrandSuggestion
from brand.models.commentary import Commentary, InstitutionCredential, InstitutionType
from brand.models.embrace_campaign import EmbraceCampaign
from brand.models.features import BrandFeature, FeatureType

from .models import Brand, Contact
from .utils.harvest_data import update_commentary_feature_data


@admin.register(Commentary)
class CommentaryAdmin(admin.ModelAdmin):
    change_form_template = "admin/brand/commentary/change_form.html"

    list_display = ["brand", "rating", "display_on_website", "feature_refresh_date"]
    readonly_fields = ["feature_yaml", "feature_refresh_date"]

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<path:object_id>/refresh/",
                self.admin_site.admin_view(self.refresh_harvest_data),
                name="refresh_harvest_data",
            )
        ]
        return custom_urls + urls

    def refresh_harvest_data(self, request, object_id):
        commentary = self.get_object(request, object_id)
        if update_commentary_feature_data(commentary, overwrite=False) is None:
            self.message_user(request, "Could not refresh Harvest data.")
        else:
            self.message_user(request, "Harvest data refreshed successfully.")
        if request.GET.get("model") == "brand":
            return redirect("admin:brand_brand_change", object_id=object_id)
        return redirect("admin:brand_commentary_change", object_id=object_id)

    def feature_yaml(self, obj):
        return format_html("<pre>{}</pre>", obj.feature_yaml)

    feature_yaml.short_description = "Feature Data (YAML)"

    def refresh_feature_data(self, request, queryset):
        for commentary in queryset:
            update_commentary_feature_data(commentary, overwrite=True)
        self.message_user(request, f"Refreshed feature data for {queryset.count()} commentaries.")

    refresh_feature_data.short_description = "Refresh feature data"

    actions = [refresh_feature_data]

    fieldsets = (
        # ... (keep existing fieldsets)
        ("Harvest Data", {"fields": ("feature_yaml", "feature_refresh_date")}),
    )


class CommentaryInline(admin.StackedInline):
    fk_name = "brand"
    model = Commentary

    @admin.display(description="Associated contact emails")
    def associated_contacts(self, obj):
        associated_contacts_qs = obj.contact_set.all()
        links = []
        links += link_contacts(associated_contacts_qs)
        links += link_contacts()
        return format_html("<br />".join(links))

    autocomplete_fields = ["inherit_brand_rating"]
    readonly_fields = (
        "rating_inherited",
        "associated_contacts",
        "feature_yaml",
        "feature_refresh_date",
    )
    fieldsets = (
        (
            "Display Configuration",
            {
                "fields": (
                    ("display_on_website", "fossil_free_alliance", "top_pick"),
                    ("rating", "show_on_sustainable_banks_page"),
                    ("rating_inherited", "inherit_brand_rating"),
                    ("embrace_campaign", "associated_contacts"),
                )
            },
        ),
        ("Used for negatively rated banks", {"fields": (("amount_financed_since_2016",))}),
        (
            "Used for positively rated banks",
            {"fields": ("institution_type", "institution_credentials")},
        ),
        ("Meta", {"fields": ("comment",)}),
    )

    def feature_yaml(self, obj):
        return format_html("<pre>{}</pre>", obj.feature_yaml)

    feature_yaml.short_description = "Feature Data (YAML)"


class BrandFeaturesInline(admin.StackedInline):
    model = BrandFeature
    fields = (("feature", "details"),)


# @admin.display(description='Name')
# def upper_case_name(obj):
#     return obj.name.upper()


# TODO make this a series of dropdowns


class BrandFeaturesReadonlyInline(admin.StackedInline):
    model = BrandFeature
    fields = (("feature", "details"),)
    readonly_fields = ["feature", "details"]


@admin.register(FeatureType)
class BrandFeatureAdmin(admin.ModelAdmin):
    search_fields = ("name", "description")
    list_display = ("name", "description")


class CountriesWidgetOverrideForm(forms.ModelForm):
    description = forms.CharField(widget=forms.Textarea(attrs={"rows": 2, "cols": 100}))
    rssd = forms.CharField(widget=forms.Textarea(attrs={"rows": 1}))
    lei = forms.CharField(widget=forms.Textarea(attrs={"rows": 1}))
    fdic_cert = forms.CharField(widget=forms.Textarea(attrs={"rows": 1}))
    ncua = forms.CharField(widget=forms.Textarea(attrs={"rows": 1}))
    permid = forms.CharField(widget=forms.Textarea(attrs={"rows": 1}))
    frn = forms.CharField(widget=forms.Textarea(attrs={"rows": 1}))

    def __init__(self, *args, **kwargs):
        super(forms.ModelForm, self).__init__(*args, **kwargs)
        self.fields["description"].required = False
        self.fields["rssd"].required = False
        self.fields["lei"].required = False
        self.fields["fdic_cert"].required = False
        self.fields["ncua"].required = False
        self.fields["permid"].required = False

    class Meta:
        widgets = {"countries": FilteredSelectMultiple("countries", is_stacked=False)}


admin.site.login_template = "registration/login.html"


class HasSuggestionsFilter(admin.SimpleListFilter):
    title = "suggested associations"
    parameter_name = "suggested associations"

    def lookups(self, request, model_admin):
        return (
            ("Any Suggestions", "Any Suggestions"),
            ("No Suggestions", "No Suggestions"),
            ("High Certainty Suggestions", "High Certainty Suggestions"),
            (" Medium Certainty Suggestions", " Medium Certainty Suggestions"),
            (" Low Certainty Suggestions", " Low Certainty Suggestions"),
        )

    # Updated HasSuggestionsFilter to use submission_date for certainty levels with BrandSuggestion
    def queryset(self, request, queryset):
        value = self.value()
        if value == "Any Suggestions":
            return queryset.filter(pk__in=BrandSuggestion.objects.values("pk"))
        elif value == "No Suggestions":
            return queryset.exclude(pk__in=BrandSuggestion.objects.values("pk"))
        elif value == "High Certainty Suggestions":
            cutoff = timezone.now() - timedelta(days=30)
            return queryset.filter(
                pk__in=BrandSuggestion.objects.filter(submission_date__gte=cutoff).values("pk")
            )
        elif value == " Medium Certainty Suggestions":
            recent_cutoff = timezone.now() - timedelta(days=30)
            older_cutoff = timezone.now() - timedelta(days=90)
            return queryset.filter(
                pk__in=BrandSuggestion.objects.filter(
                    submission_date__lt=recent_cutoff, submission_date__gte=older_cutoff
                ).values("pk")
            )
        elif value == " Low Certainty Suggestions":
            cutoff = timezone.now() - timedelta(days=90)
            return queryset.filter(
                pk__in=BrandSuggestion.objects.filter(submission_date__lt=cutoff).values("pk")
            )
        return queryset


class StatePhysicalBranchDropDownFilter(admin.SimpleListFilter):
    template = "django_admin_listfilter_dropdown/dropdown_filter.html"
    title = "state physical branch"
    parameter_name = "state_physical_branch"

    def lookups(self, request, model_admin):
        return [(s.tag, str(s)) for s in State.objects.all()]

    def queryset(self, request, queryset):
        return queryset.filter(state_physical_branch__tag__exact=self.value())


class StateLicensedDropDownFilter(admin.SimpleListFilter):
    template = "django_admin_listfilter_dropdown/dropdown_filter.html"
    title = "state licensed"
    parameter_name = "state_licensed"

    def lookups(self, request, model_admin):
        return [(s.tag, str(s)) for s in State.objects.all()]

    def queryset(self, request, queryset):
        return queryset.filter(state_licensed__tag__exact=self.value())


class ChoiceDropdownFilter(admin.ChoicesFieldListFilter):
    template = "django_admin_listfilter_dropdown/dropdown_filter.html"


@admin.register(InstitutionType)
class InstitutionTypes(admin.ModelAdmin):
    model = InstitutionType


@admin.register(InstitutionCredential)
class InstitutionCredentials(admin.ModelAdmin):
    model = InstitutionCredential


@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    search_fields = ["name"]
    list_display = ("name", "country_code", "tag")


class StateLicensedInline(admin.TabularInline):
    model = Brand.state_licensed.through
    autocomplete_fields = ["state"]
    extra = 0
    verbose_name = "State where Licensed"
    verbose_name_plural = "States where Licensed"


class StatePhysicalBranchInline(admin.TabularInline):
    model = Brand.state_physical_branch.through
    autocomplete_fields = ["state"]
    extra = 0
    verbose_name = "State where physical branch is located"
    verbose_name_plural = "States where physical branches are located"


@admin.register(Brand)
class BrandAdmin(VersionAdmin):
    form = CountriesWidgetOverrideForm
    change_list_template = "change_list_template.html"
    change_form_template = "brand_change_form.html"

    search_fields = ["name", "tag", "website"]
    readonly_fields = ["created", "modified"]
    fields = (
        ("name", "tag"),
        ("website", "aliases"),
        ("countries"),
        ("rssd", "lei"),
        ("fdic_cert", "ncua"),
        ("permid"),
        ("frn"),
        ("created", "modified"),
    )

    list_filter = (
        "commentary__display_on_website",
        "commentary__rating",
        HasSuggestionsFilter,
        ("countries", ChoiceDropdownFilter),
        StateLicensedDropDownFilter,
        StatePhysicalBranchDropDownFilter,
    )
    list_display = ("short_name", "short_tag", "pk", "website")
    list_display_links = ("short_name", "short_tag")

    list_per_page = 800

    inlines = [
        StateLicensedInline,
        StatePhysicalBranchInline,
        CommentaryInline,
        BrandFeaturesInline,
    ]

    def save_model(self, request, obj, form, change):
        """
        This function is to create object of commentary model when default values are
        provided by user in admin portal and save the data in respective database.
        """
        super().save_model(request, obj, form, change)
        try:
            obj.commentary
        except ObjectDoesNotExist as e:
            commentary_obj = Commentary.objects.create(brand_id=obj.id)
            obj.commentary = commentary_obj
            obj.save()
        update_commentary_feature_data(obj.commentary)

    def get_queryset(self, request):
        # filter out all but base class
        qs = super(BrandAdmin, self).get_queryset(request).filter(brandsuggestion__isnull=True)
        return qs

    def change_view(self, request, object_id, extra_context=None):
        brand = Brand.objects.get(id=object_id)
        extra_context = extra_context or {}
        extra_context["page_title"] = f"{Brand.objects.get(id=object_id).tag}: "
        extra_context["is_change_view"] = True
        return super(BrandAdmin, self).change_view(request, object_id, extra_context=extra_context)

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["page_title"] = "Brands: "
        extra_context["show_contact_inline"] = True
        return super(BrandAdmin, self).changelist_view(request, extra_context=extra_context)


@admin.register(BrandSuggestion)
class BrandSuggestionsAdmin(admin.ModelAdmin):
    list_display = ["short_name", "submitter_name", "submitter_email"]


@admin.register(EmbraceCampaign)
class EmbraceCampaignAdmin(admin.ModelAdmin):
    """
    This EmbraceCampaignAdmin will add EmbraceCampaign model data into
    Admin interface
    """

    form = EmbraceCampaignForm
    model = EmbraceCampaign

    list_display = ["id", "name", "configuration"]

    def get_form(self, request, obj=None, *args, **kwargs):
        form = super(EmbraceCampaignAdmin, self).get_form(request, *args, **kwargs)
        form.base_fields["configuration"].initial = {
            "email": "embracecampaign@bank.green",
            "system_prompt": "Write the system instructions here",
            "user_prompt": "write your question here",
        }
        return form


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    """
    This ContactAdmin class helps manage data from the Contact model in the admin interface.
    """

    list_display = ["id", "fullname", "email", "brand_tag", "brand_name"]
    fields = ["fullname", "email", "commentary"]
    readonly_fields = ["brand_tag", "brand_name"]
    search_fields = ["email"]

    def brand_tag(self, obj):
        if obj.brand_tag:
            brand_link = reverse(
                "admin:%s_%s_change" % ("brand", "brand"), args=(obj.commentary.brand_id,)
            )
            return format_html(f'<a href="{brand_link}">{obj.brand_tag}</a>')

    def brand_name(self, obj):
        if obj.brand_name:
            brand_link = reverse(
                "admin:%s_%s_change" % ("brand", "brand"), args=(obj.commentary.brand_id,)
            )
            return format_html(f'<a href="{brand_link}">{obj.brand_name}</a>')
