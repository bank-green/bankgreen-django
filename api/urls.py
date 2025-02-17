from django.urls import path

from brand.views import get_bank_commentary

from . import views


app_name = "rest_api"
urlpatterns = [
    path("", views.BrandSuggestionAPIView.as_view()),
    path("bank-contacts/", views.ContactView.as_view(), name="contacts"),
    path("bank/", views.BrandsView.as_view(), name="bank"),
    path("banks/<int:bank_id>/", get_bank_commentary, name="get_bank_commentary"),
]
