from django.conf.urls import url, include

from apps.game.views import CreateGame, CreateGamePlayer, ListGames, TimelineStats, ListInvitedPlayers


urlpatterns = [
    url('create', CreateGame.as_view(), name='create_game'),
    url('player', CreateGamePlayer.as_view(), name='create_player'),
    url('list', ListGames.as_view(), name='list_games'),
    url('stats', TimelineStats.as_view(), name='timeline_stats'),
    url(r'^(?P<game_id>\d+)/invitedList', ListInvitedPlayers().as_view(), name='invitedList')
]
