from django.shortcuts import render
from django.db import IntegrityError
from django.db.models import Q

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, exceptions
from rest_framework.generics import ListAPIView, CreateAPIView
from rest_framework import viewsets
from rest_framework.mixins import CreateModelMixin, ListModelMixin

from apps.game import filter_classes
from apps.game.mixins.accessMixins import LoggedInMixin
from apps.game.models import Game, GamePlayer
from apps.game.serializers import (
    CreateGameSerializer,
    CreateGamePlayerSerializer,
    GameSerializer,
    TimelineSerializer,
    InvitedPlayerSerializer,
    SocketGamePlayerSerializer,
    GameStatsSerializer
)

# Create your views here.


class GameViewset(LoggedInMixin, viewsets.GenericViewSet, CreateModelMixin, ListModelMixin,):

    filterset_class = filter_classes.GamesFilterSet

    def get_queryset(self):
        if self.action == 'list':
            return self.list_games_queryset(self.request)
        return super().get_queryset

    def get_serializer_class(self, *args, **kwargs):
        serializer_dict = {
            'create': CreateGameSerializer,
            'list': GameSerializer
        }
        return serializer_dict[self.action]

    def list_games_queryset(self, request):
        '''
        Returns queryset containing filtered list of games
        '''
        user = self.request.user
        queryset = Game.objects.filter(
            id__in=user.gameplayer_set.filter(
                Q(player_id__isnull=False)).values('game')
        )
        queryset = queryset.order_by('created_at')
        return queryset


class CreateGamePlayer(LoggedInMixin, CreateAPIView):
    '''
    Create a Player who will play the game
    '''
    serializer_class = CreateGamePlayerSerializer

# This view is WIP, and  intended for stats part of project, also WIP
# Therefore review fixes are not present here


class TimelineStats(LoggedInMixin, APIView):
    '''
    Shows User stats between two given dates
    '''

    def post(self, *args, **kwargs):
        serializer = TimelineSerializer(data=self.request.data, context={
            'user': self.request.user})
        serializer.is_valid(raise_exception=True)

        def graph(queryset):
            graph = []
            for index, row in enumerate(queryset):
                graph.append((index+1, row.created_at))
            return graph
        return Response({
            'successful_bluffs': graph(serializer.data['successful_bluffs']),
            'unsuccessful_bluffs': graph(serializer.data['unsuccessful_bluffs']),
            'games_played': graph(serializer.data['all_game_players'])
        })


class ListInvitedPlayers(LoggedInMixin, ListAPIView):
    '''
    Returns all invited players, except owner
    '''

    serializer_class = InvitedPlayerSerializer

    def get_queryset(self):
        queryset = GamePlayer.objects.filter(
            game__id=self.kwargs['game_id'], game__owner=self.request.user)
        if not queryset.exists():
            raise exceptions.ValidationError('User is not the owner of game')
        queryset = queryset.exclude(user=self.request.user)
        return queryset


class GameStats(LoggedInMixin, ListAPIView):

    serializer_class = GameStatsSerializer

    def get_queryset(self):
        game = Game.objects.filter(id=self.kwargs['game_id']).first()
        if not game:
            raise exceptions.ValidationError("This game does not exist")
        game_player = GamePlayer.objects.filter(
            game=game, user=self.request.user).first()
        if game_player is None:
            raise exceptions.ValidationError("You are not Part of this game")
        queryset = game.gameplayer_set.order_by(
            'player_id').filter(Q(player_id__isnull=False))
        return queryset

        # Status: Started,
        # owner: true,
        # Winner: ''
        # No of Players: 5,
        # Player_Name: Cards Left
