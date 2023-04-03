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
from django.urls import path, reverse_lazy
from django.views.decorators.cache import cache_control
from django.views.generic.base import RedirectView

from graphene_django.views import GraphQLView

from schema import schema

from brand import views


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", RedirectView.as_view(url=reverse_lazy("admin:index"))),
    path(
        "graphql",
        cache_control(max_age=settings.CACHE_MAX_AGE)(
            GraphQLView.as_view(graphiql=True, schema=schema)
        ),
    ),
    path("region-autocomplete/", views.RegionAutocomplete.as_view(), name="region-autocomplete"),
    path(
        "subregion-autocomplete/",
        views.SubRegionAutocomplete.as_view(),
        name="subregion-autocomplete",
    ),
    path("calendar", views.calendar_redirect, name="calendar"),
    path("update/<str:tag>/", views.CreateUpdateView.as_view(), name="update"),
    path("update_success/", views.update_success, name="update_success"),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
