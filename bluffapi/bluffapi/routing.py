from channels.routing import ProtocolTypeRouter, URLRouter
from apps.game.consumers import ChatConsumer
#from django.urls import re_path
from bluffapi.token_auth import TokenAuthMiddlewareStack
from apps.game.routing import websocket_urlpatterns
from channels.auth import AuthMiddlewareStack


application = ProtocolTypeRouter({
    # (http->django views is added by default)
    'websocket': TokenAuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})