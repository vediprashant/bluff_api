from django.conf.urls import url, include

from apps.game.views import CreateGame

urlpatterns = [
    url('create', CreateGame.as_view(), name='create_game'),
]
