from django.conf.urls import url, include
from django.contrib import admin

from apps.accounts.urls import urlpatterns as accounts_urls

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^accounts/', include(accounts_urls)),
]
