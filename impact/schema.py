import graphene
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField

from impact.models.switch_survey import SwitchSurveySubmission as SwitchSurveySubmissionModel


class SwitchSurveySubmission(DjangoObjectType):
    class Meta:
        model = SwitchSurveySubmissionModel
        fields = [
            "uuid",
            "moved_from_bank_name",
            "moved_from_brand",
            "moved_to_bank_name",
            "moved_to_brand",
            "amount",
            "currency",
            "country",
            "region",
            "created",
        ]
        interfaces = (graphene.relay.Node,)
        filter_fields = {"currency": ["exact"], "created": ["gte", "lte"]}


class Query(graphene.ObjectType):
    switch_survey_submissions = DjangoFilterConnectionField(SwitchSurveySubmission, max_limit=1000)
