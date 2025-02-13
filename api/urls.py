from django.urls import path

from . import views


app_name = "rest_api"
urlpatterns = [
    path("", views.BrandSuggestionAPIView.as_view()),
    path("bank-contacts/", views.ContactView.as_view(), name="contacts"),
    path("bank/", views.BrandsView.as_view(), name="bank"),
    path(
        "commentaries/<int:pk>/feature_override/",
        views.CommentaryFeatureOverride.as_view(),
        name="commentary_feature_override",
    ),
]
