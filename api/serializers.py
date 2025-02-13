from django_countries.fields import Country
from rest_framework import serializers

from brand.models.brand import Brand
from brand.models.brand_suggestion import BrandSuggestion
from brand.models.commentary import Commentary
from brand.models.contact import Contact


# Serialization : It is the process of converting complex data into a format that can be easily
#                 transmitted and stored. Examples : Json, XML etc.
# ModelSerializer is used for serializing Django models into Json format.


class MultipleCountryField(serializers.Field):
    def to_representation(self, obj):
        """
        Serialized method. Basically this method will convert the country field to serialized json
        format which then can be returned as a api response.
        """
        if isinstance(obj, list) and all(isinstance(item, Country) for item in obj):
            return [country.code for country in obj]
        return []

    def to_internal_value(self, data):
        """
        Deserialized method. Basically this method will convert country code from request
        payload (json format) to the format understood by django.
        """

        if not data:
            return []
        if isinstance(data, list):
            try:
                return [Country(code=code) for code in data]
            except ValueError:
                raise serializers.ValidationError("Invalid country code in the list")
        raise serializers.ValidationError("Invalid data format. Expected a list of country codes.")


class BrandSuggestionSerializer(serializers.ModelSerializer):
    countries = MultipleCountryField(required=False)  # Set required=False to make it optional

    class Meta:
        model = BrandSuggestion
        # return specific fields from model
        # fields = ('name', 'tag', 'submitter_name', "submitter_email")

        # returns all fields from model
        fields = "__all__"


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ["fullname", "email", "brand_tag"]


class CommentarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Commentary
        fields = "__all__"  # Specify the fields you want to include


class BrandSerializer(serializers.ModelSerializer):
    countries = MultipleCountryField(required=True)
    commentary = CommentarySerializer(
        read_only=True
    )  # Add the related Commentary object as a nested serializer

    class Meta:
        model = Brand
        fields = "__all__"


class CommentaryFeatureOverrideSerializer(serializers.ModelSerializer):
    class Meta:
        model = Commentary
        fields = ["feature_override"]
