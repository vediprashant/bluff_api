from django.shortcuts import render
from django.db import IntegrityError
from django.db.models import Q

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.generics import ListAPIView

from apps.game.models import Game, GamePlayer
from apps.game.serializers import CreateGameSerializer, CreateGamePlayerSerializer, GameSerializer

# Create your views here.


class CreateGame(APIView):
    '''
    Creates a new game
    '''
    permission_classes = [IsAuthenticated]

    def post(self, request):
        '''
        requires decks as input i.e no. of decks
        '''
        # create a game
        serializer = CreateGameSerializer(
            data=request.data, context=request.user)
        serializer.is_valid(raise_exception=True)
        game = serializer.save()
        return Response(game.id)


class CreateGamePlayer(APIView):
    """
    Create a Player who will play the game
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreateGamePlayerSerializer(
            data=request.data, context=request.user)
        serializer.is_valid(raise_exception=True)
        try:
            serializer.save()
        except IntegrityError as e:
            return Response({"msg": "User already invited for the game"}, status=400)
        return Response(status=201)


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
            id__in=user.gameplayer_set.all().values('game')
        )
        if 'owner' in filters:
            queryset = queryset.filter(owner=user)
        queryset = queryset.filter(started=True)
        if 'completed' in filters:
            queryset = queryset.filter(~Q(winner=None))
        queryset = queryset.order_by('created_at')
        return queryset
        