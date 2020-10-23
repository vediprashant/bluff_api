from django.conf.urls import url, include
from django.contrib import admin

from apps.accounts.urls import urlpatterns as accounts_urls
from apps.game.urls import urlpatterns as game_urls

from rest_framework_swagger.views import get_swagger_view
from rest_framework.schemas import get_schema_view

schema_view = get_swagger_view(title='BluffGame Api')

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^accounts/', include(accounts_urls)),
    url(r'^game/', include(game_urls)),
    url(r'^$', schema_view),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]
