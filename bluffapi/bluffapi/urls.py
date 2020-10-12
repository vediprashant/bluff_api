from django.conf.urls import url, include
from django.contrib import admin

from apps.accounts.urls import urlpatterns as accounts_urls
from apps.game.urls import urlpatterns as game_urls

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^accounts/', include(accounts_urls)),
    url(r'^game/', include(game_urls)),
]
