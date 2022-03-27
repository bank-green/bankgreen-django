import graphene
from graphene import relay
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from .models import Brand, Commentary


class BrandType(DjangoObjectType):
    class Meta:
        model = Brand
        filter_fields = ["countries"]
        interfaces = (relay.Node,)


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
    # commentaries2 = graphene.List(CommentaryType)

    brand = relay.Node.Field(BrandType)
    brands = DjangoFilterConnectionField(BrandType)


schema = graphene.Schema(query=Query)
