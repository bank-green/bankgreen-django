import graphene
from django_countries.graphql.types import Country
from graphene import relay
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from django_countries.graphql.types import Country
from graphene_django import DjangoListField
import django_filters
from django_filters import CharFilter, FilterSet, ChoiceFilter, BooleanFilter, MultipleChoiceFilter
from django_countries import countries
from brand.models.commentary import RatingChoice

from datasource.models.datasource import Datasource

from .models import Brand, Commentary


class DatasourceType(DjangoObjectType):
    class Meta:
        model = Datasource
        interfaces = (relay.Node,)


class BrandFilter(FilterSet):
    choices = tuple(countries)

    country = ChoiceFilter(choices=choices, method="filter_countries")

    def filter_countries(self, queryset, name, value):
        return queryset.filter(countries__contains=value)

    rating = MultipleChoiceFilter(field_name="commentary__rating", choices=RatingChoice.choices)
    recommended_only = BooleanFilter(method="filter_recommended_only")

    def filter_recommended_only(self, queryset, name, value):
        return queryset.filter(commentary__top_three_ethical=value).order_by("commentary__recommended_order")
    class Meta:
        model = Brand
        fields = []


class BrandNodeType(DjangoObjectType):
    """ """

    countries = graphene.List(Country)

    class Meta:
        model = Brand
        fields = ["tag", "name", "website", "countries"]
        interfaces = (relay.Node,)
        filterset_class = BrandFilter

class BrandType(DjangoObjectType):
    """" """
    countries = graphene.List(Country)

    class Meta:
        model = Brand
        # filter_fields = ["tag"]
        fields = ("tag", "name", "countries")
    


class CommentaryType(DjangoObjectType):
    class Meta:
        model = Commentary
        filter_fields = [
            "rating",
            "display_on_website",
            "top_three_ethical",
            "checking_saving",
            "free_checking",
            "free_atm_withdrawl",
            "online_banking",
            "local_branches",
            "mortgage_or_loan",
            "credit_cards",
            "free_international_card_payment",
        ]
        interfaces = (relay.Node,)

class Query(graphene.ObjectType):
    commentary = relay.Node.Field(CommentaryType)
    commentaries = DjangoFilterConnectionField(CommentaryType)

    brand = graphene.Field(BrandType, tag=graphene.String())
    def resolve_brand(root, info, tag):
        return Brand.objects.get(tag=tag)
    
    brands = DjangoFilterConnectionField(BrandNodeType)


schema = graphene.Schema(query=Query)
