from django.shortcuts import render

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.game.models import Game
from apps.game.serializers import CreateGameSerializer

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
        return Response(game)
