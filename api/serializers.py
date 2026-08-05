from django_countries.fields import Country
from rest_framework import serializers

from brand.models.brand import Brand
from brand.models.brand_suggestion import BrandSuggestion
from brand.models.commentary import Commentary
from brand.models.contact import Contact
from impact.models.switch_survey import SwitchSurveySubmission


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


class SingleCountryField(serializers.Field):
    def to_representation(self, obj):
        return obj.code if obj else ""

    def to_internal_value(self, data):
        if not data:
            return ""
        try:
            return Country(code=data)
        except ValueError:
            raise serializers.ValidationError("Invalid country code.")


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


class SwitchSurveySubmissionSerializer(serializers.ModelSerializer):
    moved_from_tag = serializers.CharField(required=False, write_only=True)
    moved_to_tag = serializers.CharField(required=False, write_only=True)
    email = serializers.EmailField(required=False, allow_blank=True, write_only=True)
    turnstile_token = serializers.CharField(write_only=True)
    is_agree_privacy = serializers.BooleanField(required=False, default=False)
    country = SingleCountryField(required=False, default="")

    class Meta:
        model = SwitchSurveySubmission
        fields = [
            "uuid",
            "moved_from_bank_name",
            "moved_from_tag",
            "moved_to_bank_name",
            "moved_to_tag",
            "amount",
            "currency",
            "country",
            "region",
            "created",
            "email",
            "turnstile_token",
            "is_agree_privacy",
            "is_agree_marketing",
        ]

    def validate(self, data):
        if data.get("email") and not data.get("is_agree_privacy"):
            raise serializers.ValidationError(
                {
                    "is_agree_privacy": "You must agree to the privacy policy to submit an email address."
                }
            )
        return data

    def create(self, validated_data):
        from_tag = validated_data.pop("moved_from_tag", None)
        to_tag = validated_data.pop("moved_to_tag", None)
        validated_data.pop("email", None)
        validated_data.pop("turnstile_token", None)

        tags = [tag for tag in [from_tag, to_tag] if tag]
        brands = {brand.tag: brand for brand in Brand.objects.filter(tag__in=tags)}
        validated_data["moved_from_brand"] = brands.get(from_tag)
        validated_data["moved_to_brand"] = brands.get(to_tag)

        return super().create(validated_data)


class SwitchSurveyPlanningSerializer(serializers.ModelSerializer):
    turnstile_token = serializers.CharField(write_only=True)
    is_agree_privacy = serializers.BooleanField(required=True)

    class Meta:
        model = SwitchSurveyPlanning
        fields = [
            "uuid",
            "email",
            "turnstile_token",
            "is_agree_privacy",
            "is_agree_marketing",
            "created",
        ]

    def validate_is_agree_privacy(self, value):
        if not value:
            raise serializers.ValidationError("You must agree to the privacy policy to submit.")
        return value

    def create(self, validated_data):
        validated_data.pop("turnstile_token", None)
        return super().create(validated_data)
