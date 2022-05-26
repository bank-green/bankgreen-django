import graphene
from django_countries.graphql.types import Country
from graphene import relay
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from django_countries.graphql.types import Country
from graphene_django import DjangoListField
import django_filters
from django_filters import CharFilter, FilterSet, ChoiceFilter
from django_countries import countries

from datasource.models.datasource import Datasource

from .models import Brand, Commentary


class DatasourceType(DjangoObjectType):
    class Meta:
        model = Datasource
        interfaces = (relay.Node,)


class BrandFilter(FilterSet):
    choices = tuple(countries)

    countries = ChoiceFilter(field_name="countries", choices=choices, method="filter_countries")
    headline = CharFilter(field_name="commentary_brand__headline", lookup_expr='contains', method="filter_headline")

    def filter_headline(self, queryset, name, value):
        print(value)
        return queryset.filter(commentary_brand__headline__contains=value)

    def filter_countries(self, queryset, name, value):
        print(value)
        return queryset.filter(countries__contains=value)

    
    class Meta:
        model = Brand
        fields = ["countries", "headline"]


class BrandType(DjangoObjectType):
    """ """

    countries = graphene.List(Country)

    class Meta:
        model = Brand
        exclude = []
        interfaces = (relay.Node,)
        filterset_class = BrandFilter


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

    brand = relay.Node.Field(BrandType)
    brands = DjangoFilterConnectionField(BrandType)


schema = graphene.Schema(query=Query)
