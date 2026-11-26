from django.conf import settings
from rest_framework.authentication import SessionAuthentication, TokenAuthentication


class CookieTokenAuthentication(TokenAuthentication):
    def authenticate(self, request):
        token = request.COOKIES.get(settings.TOKEN_COOKIE_NAME)
        if token:
            result = self.authenticate_credentials(token)
        else:
            result = super().authenticate(request)
        if result is not None:
            SessionAuthentication().enforce_csrf(request)
        return result

