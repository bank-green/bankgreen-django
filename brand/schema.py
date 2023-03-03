import graphene
from django_countries.graphql.types import Country
from graphene import Scalar, relay
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField, TypedFilter
from django_countries.graphql.types import Country
from graphene_django import DjangoListField
from django.db.models import Count
from django_filters import (
    FilterSet,
    ChoiceFilter,
    BooleanFilter,
    MultipleChoiceFilter,
)
from django_countries import countries
from brand.models.commentary import RatingChoice

from datasource.models.datasource import Datasource

from .models import Brand, Commentary, BrandFeature, FeatureType

from django.db.models import Q
from markdown import markdown
from markdown.extensions.footnotes import FootnoteExtension

from cities_light.models import Region, SubRegion


class DatasourceType(DjangoObjectType):
    class Meta:
        model = Datasource
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

    recommended_only = BooleanFilter(field_name="commentary__top_three_ethical")

    display_on_website = BooleanFilter(field_name="commentary__display_on_website")

    features = TypedFilter(
        method="filter_features", lookup_expr="in", input_type=graphene.List(graphene.String)
    )

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
        inheritors_qs = Brand.objects.filter(Q(pk__in=inherited_matches_pks))

        return direct_matches_qs | inheritors_qs

    class Meta:
        model = Brand
        fields = []


class RegionType(DjangoObjectType):
    class Meta:
        model = Region


class SubregionType(DjangoObjectType):
    class Meta:
        model = SubRegion


class BrandNodeType(DjangoObjectType):
    """ """

    countries = graphene.List(Country)
    regions = RegionType
    subregions = SubregionType

    class Meta:
        model = Brand
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
        ]
        interfaces = (relay.Node,)
        filterset_class = BrandFilter


class BrandType(DjangoObjectType):
    """ " """

    countries = graphene.List(Country)
    regions = RegionType
    subregions = SubregionType

    class Meta:
        model = Brand
        # filter_fields = ["tag"]
        fields = (
            "tag",
            "name",
            "website",
            "countries",
            "commentary",
            "bank_features",
            "regions",
            "subregions",
        )


class HtmlFromMarkdown(Scalar):
    """Markdown parsed into HTML"""

    @staticmethod
    def serialize(md):
        extensions = ["markdown_link_attr_modifier", FootnoteExtension()]
        extension_configs = {"markdown_link_attr_modifier": {"new_tab": "external_only"}}
        return markdown(md, extensions=extensions, extension_configs=extension_configs)


class CommentaryType(DjangoObjectType):

    recommended_in = graphene.List(Country)
    top_blurb_subheadline = HtmlFromMarkdown()
    snippet_1 = HtmlFromMarkdown()
    snippet_2 = HtmlFromMarkdown()
    snippet_3 = HtmlFromMarkdown()
    summary = HtmlFromMarkdown()
    header = HtmlFromMarkdown()
    details = HtmlFromMarkdown()
    subtitle = HtmlFromMarkdown()
    rating_inherited = graphene.Field(
        graphene.String, resolver=lambda obj, info: obj.rating_inherited
    )

    class Meta:
        model = Commentary
        filter_fields = [
            "rating",
            "display_on_website",
            "top_three_ethical",
            "show_on_sustainable_banks_page",
        ]
        interfaces = (relay.Node,)
        convert_choices_to_enum = False


class FeatureTypeType(DjangoObjectType):
    class Meta:
        model = FeatureType
        fields = "__all__"


class BrandFeatureType(DjangoObjectType):
    name = graphene.String()
    description = graphene.String()

    def resolve_name(obj, info):
        return obj.feature.name

    def resolve_description(obj, info):
        return obj.feature.description

    class Meta:
        model = BrandFeature
        fields = "__all__"
        convert_choices_to_enum = False


class Query(graphene.ObjectType):
    commentary = relay.Node.Field(CommentaryType)
    commentaries = DjangoFilterConnectionField(CommentaryType)

    brand = graphene.Field(BrandType, tag=graphene.String())

    def resolve_brand(root, info, tag):
        return Brand.objects.get(tag=tag)

    brands = DjangoFilterConnectionField(BrandNodeType)

    features = DjangoListField(FeatureTypeType)


schema = graphene.Schema(query=Query)
