from django.db import transaction

from rest_framework import serializers

from apps.game.models import Game, GamePlayer, GameTableSnapshot


class CreateGameSerializer(serializers.Serializer):
    '''
    validates 3 >= decks >= 1
    creates a game
    '''
    decks = serializers.IntegerField(
        max_value=3,
        min_value=1
    )

    class Meta:
        fields = ['decks']

    def create(self, validated_data):
        with transaction.atomic():
            game = Game.objects.create(
                started=False,
                owner=self.context,
                winner=None,
                decks=validated_data['decks']
            )
            game_player = GamePlayer.objects.create(
                user=self.context,
                game=game,
                player_id=1,
                disconnected=True,
                noAction=0,
                cards='0'*game.decks*52,
            )
            GameTableSnapshot.objects.create(
                game=game,
                currentSet='1'*game.decks*52,  # any card is valid
                cardsOnTable='1'*game.decks*52,  # all cards on table
                lastCards='0'*game.decks*52,
                lastUser=None,
                currentUser=None,
                bluffCaller=None,
                bluffSuccessful=None,
                didSkip=None
            )
        return game
