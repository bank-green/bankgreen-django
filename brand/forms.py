from dal import autocomplete
from django import forms

from .models import BrandFeature


class BrandFeaturesForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(BrandFeaturesForm, self).__init__(*args, **kwargs)

        self.fields["feature"].widget.attrs["class"] = "form-select"
        self.fields["details"].widget.attrs["class"] = "form-control"

    class Meta:
        model = BrandFeature
        fields = ["details", "feature"]
