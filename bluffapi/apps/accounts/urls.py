from rest_framework import routers

from django.conf.urls import url, include

from apps.accounts import views as accounts_views

accounts_router = routers.DefaultRouter()
accounts_router.register(r'users', accounts_views.UserViewSet)

urlpatterns = [
    url(r'^login/', accounts_views.Login.as_view())
]
urlpatterns += accounts_router.urls