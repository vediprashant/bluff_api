from django.contrib import admin

from apps.game import models as game_models
admin.site.register(game_models.Game)
admin.site.register(game_models.GamePlayer)
admin.site.register(game_models.GameTableSnapshot)
