import graphene
from django_filters import DateFilter, FilterSet
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField

from impact.models.switch_survey import SwitchSurveySubmission as SwitchSurveySubmissionModel


class SwitchSurveySubmissionFilter(FilterSet):
    # Date granularity, not datetime. A datetime filter would let a caller binary
    # search the exact submission time of a row that only reports its date.
    created__gte = DateFilter(field_name="created", lookup_expr="date__gte")
    created__lte = DateFilter(field_name="created", lookup_expr="date__lte")

    class Meta:
        model = SwitchSurveySubmissionModel
        fields = ["currency"]


class SwitchSurveySubmission(DjangoObjectType):
    # Reported as a UTC date. The stored time of day narrows a row to a single
    # respondent, so it is not published.
    created = graphene.Date(required=True)

    class Meta:
        model = SwitchSurveySubmissionModel
        fields = [
            "moved_from_bank_name",
            "moved_from_brand",
            "moved_to_bank_name",
            "moved_to_brand",
            "amount",
            "currency",
            "country",
            "created",
        ]
        # No relay.Node interface, so the type carries no id field and the
        # database primary key stays private. Pagination still works because
        # connection cursors are array offsets.
        use_connection = True
        filterset_class = SwitchSurveySubmissionFilter

    def resolve_created(self, info):
        return self.created.date()


class Query(graphene.ObjectType):
    switch_survey_submissions = DjangoFilterConnectionField(SwitchSurveySubmission, max_limit=1000)
