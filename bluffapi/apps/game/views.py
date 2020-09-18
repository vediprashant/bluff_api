from django.shortcuts import render
from django.db import IntegrityError

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from apps.game.models import Game
from apps.game.serializers import CreateGameSerializer, CreateGamePlayerSerializer

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
        return Response({'id': game.id}, status=status.HTTP_201_CREATED)


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
