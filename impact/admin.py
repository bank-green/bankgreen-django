from django.contrib import admin

from impact.models.switch_survey_emails import SwitchSurveyEmail
from impact.models.switch_survey import SwitchSurveySubmission
from impact.models.switch_survey_planning import SwitchSurveyPlanning


@admin.register(SwitchSurveySubmission)
class SwitchSurveySubmissionAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "uuid",
        "moved_from_bank_name",
        "moved_to_bank_name",
        "amount",
        "currency",
        "is_agree_privacy",
        "is_agree_marketing",
        "created",
    ]


@admin.register(SwitchSurveyEmail)
class SwitchSurveyEmailAdmin(admin.ModelAdmin):
    list_display = ["id", "email", "submission", "mailerlite_synced", "created"]
    list_select_related = ["submission"]


@admin.register(SwitchSurveyPlanning)
class SwitchSurveyPlanningAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "uuid",
        "email",
        "is_agree_privacy",
        "is_agree_marketing",
        "mailerlite_synced",
        "created",
    ]
