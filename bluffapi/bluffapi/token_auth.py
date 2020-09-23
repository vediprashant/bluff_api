from channels.auth import AuthMiddlewareStack
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import AnonymousUser


class TokenAuthMiddleware:
    """
    Token authorization middleware for Django Channels 2
    """

    def __init__(self, inner):
        self.inner = inner

    def __call__(self, scope):
        headers = dict(scope['headers'])
        try:
            key = str(headers[b'cookie']).split('=')[-1][:-1]
            token = Token.objects.get(key=key)
            scope['user'] = token.user
        except:
            scope['user'] = AnonymousUser()
        return self.inner(scope)

def TokenAuthMiddlewareStack(inner): return TokenAuthMiddleware(
    AuthMiddlewareStack(inner))
