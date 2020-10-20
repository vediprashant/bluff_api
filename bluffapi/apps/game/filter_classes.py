import django_filters
from apps.game import models as game_models


class GamesFilterSet(django_filters.FilterSet):
    '''
    Class to filter games based on it's status
    '''
    completed = django_filters.BooleanFilter(
        field_name='winner', lookup_expr='isnull')

    class Meta:
        model = game_models.Game
        fields = ['completed']
