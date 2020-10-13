from django.shortcuts import render
from django.db import IntegrityError
from django.db.models import Q

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, exceptions
from rest_framework.generics import ListAPIView, CreateAPIView

from apps.game.models import Game, GamePlayer
from apps.game.serializers import (
    CreateGameSerializer,
    CreateGamePlayerSerializer,
    GameSerializer,
    TimelineSerializer,
    InvitedPlayerSerializer,
)

# Create your views here.


class CreateGame(CreateAPIView):
    '''
    Creates a new game
    takes number of decks as input
    '''
    permission_classes = [IsAuthenticated]
    serializer_class = CreateGameSerializer


class CreateGamePlayer(APIView):
    '''
    Create a Player who will play the game
    '''
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreateGamePlayerSerializer(
            data=request.data, context=request.user)
        serializer.is_valid(raise_exception=True)
        try:
            serializer.save()
        except IntegrityError as e:
            return Response({'msg': 'User already invited for the game'}, status=400)
        return Response(status=status.HTTP_201_CREATED)


class ListGames(ListAPIView):
    '''
    Lists and filters All games related to user
    '''
    permission_classes = [IsAuthenticated]
    serializer_class = GameSerializer

    def get_queryset(self, *args, **kwargs):
        user = self.request.user
        filters = self.request.GET.getlist('filters')
        queryset = Game.objects.filter(
            id__in=user.gameplayer_set.filter(Q(player_id__isnull=False)).values('game')
        )
        if 'owner' in filters:
            queryset = queryset.filter(owner=user)
        if 'completed' in filters:
            queryset = queryset.filter(Q(winner__isnull=False))
        else:
            queryset = queryset.filter(Q(winner__isnull=True))
        queryset = queryset.order_by('created_at')
        return queryset


class TimelineStats(APIView):
    '''
    Shows User stats between two given dates
    '''
    permission_classes = [IsAuthenticated]

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


class ListInvitedPlayers(ListAPIView):
    '''
    Returns all invited players, except owner
    '''
    permission_classes = [IsAuthenticated]

    serializer_class = InvitedPlayerSerializer

    def get_queryset(self):
        queryset = GamePlayer.objects.filter(
            game__id=self.kwargs['game_id'], game__owner=self.request.user)
        if not queryset.exists():
            raise exceptions.ValidationError('User is not the owner of game')
        queryset = queryset.exclude(user=self.request.user)
        return queryset
