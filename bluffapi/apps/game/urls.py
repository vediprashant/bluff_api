from django.conf.urls import url, include

from rest_framework import routers

from apps.game.views import (
    CreateGamePlayer,
    TimelineStats,
    ListInvitedPlayers,
    GameViewset,
    GameStats
)

router = routers.SimpleRouter()
router.register(r'', GameViewset, basename='game')

urlpatterns = [
    url('player', CreateGamePlayer.as_view(), name='create_player'),
    url('stats', TimelineStats.as_view(), name='timeline_stats'),
    url(r'^(?P<game_id>\d+)/invitedList',
        ListInvitedPlayers().as_view(), name='invitedList'),
    url(r'^(?P<game_id>\d+)/info',
        GameStats.as_view(), name='game_stats')
]
urlpatterns += (router.urls)
