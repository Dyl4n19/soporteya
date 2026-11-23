from django.conf import settings
from rest_framework.authentication import SessionAuthentication, TokenAuthentication


class CookieTokenAuthentication(TokenAuthentication):
    def authenticate(self, request):
        token = request.COOKIES.get(settings.TOKEN_COOKIE_NAME)
        if not token:
            return None
        result = self.authenticate_credentials(token)
        SessionAuthentication().enforce_csrf(request)
        return result

