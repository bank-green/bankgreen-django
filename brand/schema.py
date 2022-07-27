import graphene
from django_countries.graphql.types import Country
from graphene import Scalar, relay
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from django_countries.graphql.types import Country
from graphene_django import DjangoListField
import django_filters
from django_filters import (
    CharFilter,
    FilterSet,
    ChoiceFilter,
    BooleanFilter,
    MultipleChoiceFilter,
    OrderingFilter,
)
from django_countries import countries
from brand.models.commentary import RatingChoice

from datasource.models.datasource import Datasource

from .models import Brand, Commentary, Features, BrandFeature, FeatureType

from markdown import markdown


class DatasourceType(DjangoObjectType):
    class Meta:
        model = Datasource
        interfaces = (relay.Node,)


class BrandFilter(FilterSet):
    choices = tuple(countries)

    country = ChoiceFilter(choices=choices, method="filter_countries")

    def filter_countries(self, queryset, name, value):
        return queryset.filter(countries__contains=value).order_by("name")

    rating = MultipleChoiceFilter(field_name="commentary__rating", choices=RatingChoice.choices)
    recommended_only = BooleanFilter(field_name="commentary__top_three_ethical")

    display_on_website = BooleanFilter(field_name="commentary__display_on_website")

    class Meta:
        model = Brand
        fields = []


class BrandNodeType(DjangoObjectType):
    """ """

    countries = graphene.List(Country)

    class Meta:
        model = Brand
        fields = ["tag", "name", "website", "countries", "commentary", "features", "bank_features"]
        interfaces = (relay.Node,)
        filterset_class = BrandFilter


class BrandType(DjangoObjectType):
    """ " """

    countries = graphene.List(Country)

    class Meta:
        model = Brand
        # filter_fields = ["tag"]
        fields = ("tag", "name", "website", "countries", "commentary", "features", "bank_features")


class HtmlFromMarkdown(Scalar):
    """Markdown parsed into HTML"""

    @staticmethod
    def serialize(md):
        extensions = ["markdown_link_attr_modifier"]
        extension_configs = {"markdown_link_attr_modifier": {"new_tab": "external_only"}}
        return markdown(md, extensions=extensions, extension_configs=extension_configs)


class CommentaryType(DjangoObjectType):

    recommended_in = graphene.List(Country)
    top_blurb_subheadline = HtmlFromMarkdown()
    snippet_1 = HtmlFromMarkdown()
    snippet_2 = HtmlFromMarkdown()
    snippet_3 = HtmlFromMarkdown()

    class Meta:
        model = Commentary
        filter_fields = ["rating", "display_on_website", "top_three_ethical"]
        interfaces = (relay.Node,)


class FeaturesType(DjangoObjectType):
    class Meta:
        model = Features
        filter_fields = [
            "checking_saving",
            "free_checking",
            "free_atm_withdrawal",
            "online_banking",
            "local_branches",
            "mortgage_or_loan",
            "credit_cards",
            "free_international_card_payment",
        ]
        interfaces = (relay.Node,)


class FeatureTypeType(DjangoObjectType):
    class Meta:
        model = FeatureType
        fields = "__all__"


class BrandFeatureType(DjangoObjectType):
    class Meta:
        model = BrandFeature
        fields = "__all__"


class Query(graphene.ObjectType):
    commentary = relay.Node.Field(CommentaryType)
    commentaries = DjangoFilterConnectionField(CommentaryType)
    features = relay.Node.Field(FeaturesType)

    brand = graphene.Field(BrandType, tag=graphene.String())

    def resolve_brand(root, info, tag):
        return Brand.objects.get(tag=tag)

    brands = DjangoFilterConnectionField(BrandNodeType)


schema = graphene.Schema(query=Query)
