import graphene
from graphene import Scalar, relay
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField, TypedFilter
from django_countries.graphql.types import Country
from graphene_django import DjangoListField
from django.db.models import Count
from django_filters import FilterSet, ChoiceFilter, BooleanFilter, MultipleChoiceFilter
from django_countries import countries
from brand.models.commentary import RatingChoice

from datasource.models.datasource import Datasource as DatasourceModel

from .models import (
    Brand as BrandModel,
    Commentary as CommentaryModel,
    BrandFeature as BrandFeatureModel,
    FeatureType as FeatureModel,
)

from .models.commentary import (
    InstitutionType as InstitutionTypeModel,
    InstitutionCredential as InstitutionCredentialModel,
)

from django.db.models import Q
from markdown import markdown
from markdown.extensions.footnotes import FootnoteExtension

from cities_light.models import Region as RegionModel, SubRegion as SubRegionModel


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


class Commentary(DjangoObjectType):
    summary = HtmlFromMarkdown()
    header = HtmlFromMarkdown()
    details = HtmlFromMarkdown()
    subtitle = HtmlFromMarkdown()
    rating_inherited = graphene.Field(
        graphene.String, resolver=lambda obj, info: obj.rating_inherited
    )
    top_pick = graphene.Boolean()

    def resolve_top_pick(obj, info):
        return obj.top_pick

    class Meta:
        model = CommentaryModel
        filter_fields = ["rating", "display_on_website", "show_on_sustainable_banks_page"]
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


class Query(graphene.ObjectType):
    node = relay.Node.Field()
    commentary = relay.Node.Field(Commentary)
    commentaries = DjangoFilterConnectionField(Commentary)

    brand = graphene.Field(Brand, tag=graphene.Argument(graphene.String, required=True))

    def resolve_brand(root, info, tag):
        return BrandModel.objects.get(tag=tag)

    brands = DjangoFilterConnectionField(Brand)

    features = DjangoListField(Feature)


schema = graphene.Schema(query=Query)
