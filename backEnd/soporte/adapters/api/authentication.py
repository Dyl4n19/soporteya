from django.conf import settings
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed


class CookieTokenAuthentication(TokenAuthentication):
    def authenticate(self, request):
        header_result = super().authenticate(request)
        if header_result:
            return header_result
        token = request.COOKIES.get(settings.TOKEN_COOKIE_NAME)
        if not token:
            return None
        try:
            result = self.authenticate_credentials(token)
            SessionAuthentication().enforce_csrf(request)
            return result
        except AuthenticationFailed:
            return None

