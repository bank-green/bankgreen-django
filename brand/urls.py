from django.urls import path
from .views import get_bank_commentary  # Import the API view

urlpatterns = [
    path("banks/<int:bank_id>/", get_bank_commentary, name="get_bank_commentary"),
]
