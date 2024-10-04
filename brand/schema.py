import ast
import json
import logging

from django.db.models import Case, Count, Q, When

import graphene
from cities_light.models import Region as RegionModel
from cities_light.models import SubRegion as SubRegionModel
from django_countries import countries
from django_countries.graphql.types import Country
from django_filters import BooleanFilter, ChoiceFilter, FilterSet, MultipleChoiceFilter
from graphene import Scalar, relay
from graphene_django import DjangoListField, DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField, TypedFilter
from graphql import GraphQLError
from markdown import markdown
from markdown.extensions.footnotes import FootnoteExtension

from brand.models.commentary import RatingChoice
from datasource.models.datasource import Datasource as DatasourceModel
from utils.brand_utils import fetch_cached_harvest_data, filter_json_field

from .models import Brand as BrandModel
from .models import BrandFeature as BrandFeatureModel
from .models import Commentary as CommentaryModel
from .models import EmbraceCampaign as EmbraceCampaignModel
from .models import FeatureType as FeatureModel
from .models.commentary import InstitutionCredential as InstitutionCredentialModel
from .models.commentary import InstitutionType as InstitutionTypeModel


logger = logging.getLogger(__name__)


class Datasource(DjangoObjectType):
    subclass = graphene.String()

    def resolve_subclass(obj, info):
        try:
            return type(obj.subclass()).__name__
        except NotImplementedError:
            return None

    class Meta:
        model = DatasourceModel
        fields = ("name", "source_link")
        interfaces = (relay.Node,)


class BrandFilter(FilterSet):
    choices = tuple(countries)

    country = ChoiceFilter(choices=choices, method="filter_countries")

    def filter_countries(self, queryset, name, value):
        return queryset.filter(countries__contains=value).order_by("name")

    regions = TypedFilter(
        method="filter_regions", lookup_expr="in", input_type=graphene.List(graphene.String)
    )

    def filter_regions(self, queryset, name, value):
        return queryset.filter(
            Q(regions__name_ascii__in=value) | Q(regions__geoname_code__in=value)
        )

    subregions = TypedFilter(
        method="filter_subregions", lookup_expr="in", input_type=graphene.List(graphene.String)
    )

    def filter_subregions(self, queryset, name, value):
        return queryset.filter(
            Q(subregions__name_ascii__in=value) | Q(subregions__geoname_code__in=value)
        )

    rating = MultipleChoiceFilter(
        method="filter_rating", field_name="commentary__rating", choices=RatingChoice.choices
    )

    # rating_inherited = MultipleChoiceFilter(field_name="commentary__rating_inherited", choices=RatingChoice.choices)

    recommended_only = BooleanFilter(
        field_name="commentary__show_on_sustainable_banks_page", method="filter_recommended"
    )

    def filter_recommended(self, queryset, name, value):
        # Return banks with 'show_on_sustainable_banks_page' and order results
        # by those with top_pick first, then fossil_free_alliance, then
        # sort on direct ratings, and finally list those with inherited
        # ratings if any. Since inherited ratings can't be accessed in db query,
        # ordering that includes inherited rating would be better done on the
        # client side. This provides a decent default though.

        # Treat 'recommendedOnly: false' as if filter wasn't included
        if value is False:
            return queryset

        recommended_qs = queryset.filter(commentary__show_on_sustainable_banks_page=True)

        # Add a numerical rank for direct ratings so we can then use it to sort
        # appropriately.
        recommended_qs = recommended_qs.annotate(
            rating_num=Case(
                When(commentary__rating=RatingChoice.GREAT, then=1),
                When(commentary__rating=RatingChoice.GOOD, then=10),
                When(commentary__rating=RatingChoice.OK, then=100),
                default=100000,
            )
        ).order_by("-commentary__top_pick", "-commentary__fossil_free_alliance", "rating_num")

        return recommended_qs

    display_on_website = BooleanFilter(field_name="commentary__display_on_website")

    features = TypedFilter(
        method="filter_features", lookup_expr="in", input_type=graphene.List(graphene.String)
    )

    top_pick = BooleanFilter(field_name="commentary__top_pick")

    fossil_free_alliance = BooleanFilter(field_name="commentary__fossil_free_alliance")

    def filter_features(self, queryset, name, value):
        # return all brands that have "Yes" or "Maybe" for all given features
        return (
            queryset.filter(
                bank_features__feature__name__in=value, bank_features__offered__in=["Yes", "Maybe"]
            )
            .annotate(num_feats=Count("bank_features"))
            .filter(num_feats=len(value))
        )

    def filter_rating(self, queryset, name, value):
        # ratings matching the query exactly
        direct_matches_qs = queryset.filter(commentary__rating__in=value)

        # some brands have inherited ratings defined as a property
        inherited_matches_pks = [
            x.pk
            for x in queryset.filter(commentary__rating=RatingChoice.INHERIT)
            if x.commentary.rating_inherited in value
        ]

        inheritors_qs = queryset.filter(Q(pk__in=inherited_matches_pks))

        return direct_matches_qs | inheritors_qs

    class Meta:
        model = BrandModel
        fields = []


class Region(DjangoObjectType):
    class Meta:
        model = RegionModel


class SubRegion(DjangoObjectType):
    class Meta:
        model = SubRegionModel


class Brand(DjangoObjectType):
    """ """

    countries = graphene.List(Country)
    regions = Region
    subregions = SubRegion

    class Meta:
        model = BrandModel
        fields = [
            "tag",
            "name",
            "website",
            "countries",
            "commentary",
            "bank_features",
            "aliases",
            "regions",
            "subregions",
            "datasources",
        ]
        interfaces = (relay.Node,)
        filterset_class = BrandFilter


class HtmlFromMarkdown(Scalar):
    """Markdown parsed into HTML"""

    @staticmethod
    def serialize(md):
        extensions = ["markdown_link_attr_modifier", FootnoteExtension()]
        extension_configs = {"markdown_link_attr_modifier": {"new_tab": "external_only"}}
        return markdown(md, extensions=extensions, extension_configs=extension_configs)


class InstitutionTypeType(DjangoObjectType):
    class Meta:
        model = InstitutionTypeModel


class InstitutionCredentialType(DjangoObjectType):
    class Meta:
        model = InstitutionCredentialModel


class JSONScalar(Scalar):
    @staticmethod
    def serialize(value):
        return json.loads(value)

    @staticmethod
    def parse_literal(node):
        if isinstance(node, ast.StringValue):
            return json.loads(node.value)

    @staticmethod
    def parse_value(value):
        return json.loads(value)


class HarvestData(graphene.ObjectType):
    customers_served = JSONScalar()
    deposit_products = JSONScalar()
    financial_features = JSONScalar()
    services = JSONScalar()
    institutional_information = JSONScalar()
    policies = JSONScalar()
    loan_products = JSONScalar()
    interest_rates = JSONScalar()


class Commentary(DjangoObjectType):
    summary = HtmlFromMarkdown()
    header = HtmlFromMarkdown()
    details = HtmlFromMarkdown()
    subtitle = HtmlFromMarkdown()
    rating_inherited = graphene.Field(
        graphene.String, resolver=lambda obj, info: obj.rating_inherited
    )
    top_pick = graphene.Boolean()
    harvest_data = graphene.Field(HarvestData)

    def resolve_top_pick(obj, info):
        return obj.top_pick

    def resolve_harvest_data(self, info):
        try:
            return fetch_cached_harvest_data(self.brand.tag)
        except Exception as e:
            logging.error(f"Error fetching harvest data for {self.brand.tag}: {str(e)}")
            return None

    class Meta:
        model = CommentaryModel
        filter_fields = [
            "rating",
            "display_on_website",
            "show_on_sustainable_banks_page",
            "embrace_campaign",
        ]
        interfaces = (relay.Node,)
        convert_choices_to_enum = False


class Feature(DjangoObjectType):
    class Meta:
        model = FeatureModel
        fields = "__all__"


class BrandFeature(DjangoObjectType):
    name = graphene.String()
    description = graphene.String()

    def resolve_name(obj, info):
        return obj.feature.name

    def resolve_description(obj, info):
        return obj.feature.description

    class Meta:
        model = BrandFeatureModel
        fields = "__all__"
        convert_choices_to_enum = False


class EmbraceCampaignType(DjangoObjectType):
    class Meta:
        model = EmbraceCampaignModel
        fields = ("id", "name", "description", "configuration")


class Query(graphene.ObjectType):
    node = relay.Node.Field()
    commentary = relay.Node.Field(Commentary)
    commentaries = DjangoFilterConnectionField(Commentary)

    brand = graphene.Field(Brand, tag=graphene.Argument(graphene.String, required=True))

    brand_by_name = graphene.Field(Brand, name=graphene.Argument(graphene.String, required=True))

    embrace_campaigns = graphene.List(EmbraceCampaignType)

    brands_filtered_by_embrace_campaign = graphene.List(
        Brand, id=graphene.Argument(graphene.Int, required=True)
    )

    harvest_data = graphene.Field(
        HarvestData,
        tag=graphene.String(required=True),
        customers_served=graphene.String(),
        deposit_products=graphene.String(),
        financial_features=graphene.String(),
        services=graphene.String(),
        institutional_information=graphene.String(),
        policies=graphene.String(),
        loan_products=graphene.String(),
        interest_rates=graphene.String(),
    )

    def resolve_brand(root, info, tag):
        return BrandModel.objects.get(tag=tag)

    def resolve_brand_by_name(root, info, name):
        return BrandModel.objects.get(name=name)

    def resolve_embrace_campaigns(root, info):
        return EmbraceCampaignModel.objects.all()

    def resolve_brands_filtered_by_embrace_campaign(root, info, id):
        embrace_campaign_obj = EmbraceCampaignModel.objects.get(id=id)
        brand_countries = []
        for commentary_obj in embrace_campaign_obj.commentary_set.all():
            brand_countries.append(
                {
                    "name": commentary_obj.brand.name,
                    "website": commentary_obj.brand.website,
                    "tag": commentary_obj.brand.tag,
                    "aliases": commentary_obj.brand.aliases,
                    "countries": commentary_obj.brand.countries,
                }
            )
        return [Brand(**brand_data) for brand_data in brand_countries]

    def resolve_harvest_data(self, info, tag, **kwargs):
        try:
            cached_data = fetch_cached_harvest_data(tag)

            # Apply filters
            filtered_data = {}
            for field, value in kwargs.items():
                if field in cached_data:
                    filtered_data[field] = filter_json_field(cached_data[field], value)
                else:
                    logger.warning(f"Field '{field}' not found for brand tag: {tag}")

            # If no fields were successfully filtered, raise an error
            if not filtered_data:
                raise GraphQLError(f"No matching data found for brand tag: {tag}")

            return HarvestData(**filtered_data)
        except requests.RequestException as e:
            logger.error(f"Error fetching harvest data for {tag}: {str(e)}")
            raise GraphQLError(f"Failed to fetch harvest data: {str(e)}") from e
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding harvest data for {tag}: {str(e)}")
            raise GraphQLError("Invalid data received from harvest API") from e
        except Exception as e:
            logger.error(f"Unexpected error resolving harvest data for {tag}: {str(e)}")
            raise GraphQLError("An unexpected error occurred while fetching harvest data") from e

    brands = DjangoFilterConnectionField(Brand)

    features = DjangoListField(Feature)


schema = graphene.Schema(query=Query)
