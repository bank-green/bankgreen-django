from dal import autocomplete
from django import forms

from .models import BrandUpdate, BrandFeature
from cities_light.models import Region, SubRegion


class CreateUpdateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(CreateUpdateForm, self).__init__(*args, **kwargs)

        self.fields["countries"].widget.attrs["class"] = "form-select"
        self.fields["regions"].widget.attrs["class"] = "form-select"
        self.fields["subregions"].widget.attrs["class"] = "form-select"
        self.fields["additional_info"].widget.attrs["class"] = "form-control"
        self.fields["consent"].widget.attrs["class"] = "form-check-input"

    class Meta:
        model = BrandUpdate
        fields = BrandUpdate.UPDATE_FIELDS + ["additional_info", "email", "consent"]
        widgets = {
            "regions": autocomplete.ModelSelect2Multiple(
                url="region-autocomplete",
                attrs={
                    # Set some placeholder
                    "data-placeholder": "Start typing...",
                    # Only trigger autocompletion after 3 characters have been typed
                    "data-minimum-input-length": 3,
                },
            ),
            "subregions": autocomplete.ModelSelect2Multiple(
                url="subregion-autocomplete",
                attrs={
                    # Set some placeholder
                    "data-placeholder": "Start typing...",
                    # Only trigger autocompletion after 3 characters have been typed
                    "data-minimum-input-length": 3,
                },
            ),
        }


class BrandFeaturesForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(BrandFeaturesForm, self).__init__(*args, **kwargs)

        self.fields["feature"].widget.attrs["class"] = "form-select"
        self.fields["offered"].widget.attrs["class"] = "form-select"
        self.fields["details"].widget.attrs["class"] = "form-control"

    class Meta:
        model = BrandFeature
        fields = ["offered", "details", "feature"]
