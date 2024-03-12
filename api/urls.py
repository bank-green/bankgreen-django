from django.urls import path
from . import views


urlpatterns = [path("", views.BrandSuggestionAPIView.as_view()),
               path("brand_info", views.BrandGetTag.as_view())]
