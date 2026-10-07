from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

class APIKeyAuthentication(BaseAuthentication):
    keyword = "Api-Key"

    def authenticate(self, request):
        if not settings.API_AUTH_ENABLED:
            return None
        key = request.headers.get("X-API-Key")
        if not key or key != settings.API_KEY:
            raise AuthenticationFailed("Invalid API key.")
        return (None, key)
