"""bankgreen URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, re_path, reverse_lazy, include
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import RedirectView

from graphene_django.views import GraphQLView

from schema import schema

from brand import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", RedirectView.as_view(url=reverse_lazy("admin:index"))),
    re_path(
        "^graphql/?$",
        cache_control(max_age=settings.CACHE_MAX_AGE)(
            csrf_exempt(GraphQLView.as_view(graphiql=True, schema=schema))
        ),
    ),
    path("region-autocomplete/", views.RegionAutocomplete.as_view(), name="region-autocomplete"),
    path(
        "subregion-autocomplete/",
        views.SubRegionAutocomplete.as_view(),
        name="subregion-autocomplete",
    ),
    path("calendar/", views.calendar_redirect, name="calendar"),
    path("update/<str:tag>/", views.CreateUpdateView.as_view(), name="update"),
    path("banks/<str:tag>/", views.brand_redirect, name="brand_quicklink"),
    path("sustainable-eco-banks/<str:tag>/", views.brand_redirect, name="brand_quicklink"),
    path("update_success/", views.update_success, name="update_success"),
    path("rest_api_view/", include("api.urls")),
    path("check-duplicates/", views.check_duplicates, name="check_duplicates"),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
