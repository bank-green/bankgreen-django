from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings


class SingleTokenAuthentication(TokenAuthentication):
    def authenticate(self, request) -> None:
        request_token = request.headers["Authorization"].split(" ")[-1]

        if request_token == settings.REST_API_CONTACT_SINGLE_TOKEN:
            return None
        raise AuthenticationFailed("Invalid token")
