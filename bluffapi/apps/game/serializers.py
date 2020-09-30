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

    def initial_cards(self, decks):
        if decks == 1:
            return '100'*52
        elif decks == 2:
            return '110'*52
        else:
            return '111'*52

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
                cards='0'*156,  # Player has no cards initially
            )
            GameTableSnapshot.objects.create(
                game=game,
                currentSet=None,
                cardsOnTable=self.initial_cards(game.decks), #All cards on table
                lastCards='0'*156, #no last cards
                lastUser=None,
                currentUser=None,
                bluffCaller=None,
                bluffSuccessful=None,
                didSkip=None
            )

        return game
