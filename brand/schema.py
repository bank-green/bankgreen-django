import graphene
from graphene_django import DjangoObjectType
from .models import Brand, Commentary


class BrandType(DjangoObjectType):
    class Meta:
        model = Brand


class CommentaryType(DjangoObjectType):
    class Meta:
        model = Commentary


class Query(graphene.ObjectType):
    commentaries = graphene.List(CommentaryType)
    brands = graphene.List(BrandType)

    def resolve_commentaries(self, info, **kwargs):
        return Commentary.objects.all()

    def resolve_brands(self, info, **kwargs):
        return Brand.objects.all()


schema = graphene.Schema(query=Query)
