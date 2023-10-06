from django.urls import path
from . import views


urlpatterns = [path("", views.BrandSuggestionAPIView.as_view()),]
