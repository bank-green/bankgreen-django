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
        print(value)
        return queryset.filter(countries__contains=value)

    rating = MultipleChoiceFilter(field_name="commentary__rating", choices=RatingChoice.choices)
    top_three_ethical = BooleanFilter(field_name="commentary__top_three_ethical", )


    class Meta:
        model = Brand
        fields = []


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
