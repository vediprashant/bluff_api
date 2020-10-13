from django.conf.urls import url

from apps.game import consumers as game_consumers

websocket_urlpatterns = [
    url(r'ws/chat/(?P<game_id>\w+)/$', game_consumers.GameConsumer),
]
