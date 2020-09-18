from django.db import transaction

from rest_framework import serializers, exceptions

from apps.game.models import Game, GamePlayer, GameTableSnapshot
from apps.accounts import models as accounts_model


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
            GamePlayer.objects.create(
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
                cardsOnTable='1'*game.decks*52+'0' *
                (3-game.decks)*52,  # All cards on table
                lastCards='0'*156,  # no last cards
                lastUser=None,
                currentUser=None,
                bluffCaller=None,
                bluffSuccessful=None,
                didSkip=None
            )
        return game


class CreateGamePlayerSerializer(serializers.Serializer):
    email = serializers.EmailField()
    game = serializers.IntegerField()

    def validate(self, data):
        email = data.get('email')
        user = accounts_model.User.objects.filter(email=email).first()
        if user:
            data['user'] = user
        else:
            msg = "User not found, Please provide Valid email or ask the user to Sign Up"
            raise exceptions.ValidationError(msg)
        game = Game.objects.filter(pk=data.get('game')).first()
        if game and game.owner == self.context:
            data['game'] = game
        else:
            msg = "Game id not found, Please provide Valid Input"
            raise exceptions.ValidationError(msg)
        return super(CreateGamePlayerSerializer, self).validate(data)

    def create(self, validated_data):
        validated_data.pop('email')
        validated_data['cards'] = '0'*(validated_data['game'].decks*52)
        instance = GamePlayer.objects.create(**validated_data)
        return instance


class GameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Game
        fields = ['id', 'created_at']


class SocketInitSerializer(serializers.Serializer):
    '''
    Game must exist
    User must be a game player of Game
    '''
    game = serializers.IntegerField(
        min_value=1
    )
    user = serializers.IntegerField(
        min_value=1
    )

    class Meta:
        fields = ['game', 'user']

    def validate_game(self, value):
        '''
        checks if game exists
        returns game object
        '''
        if not Game.objects.filter(id=value).exists():
            raise exceptions.ValidationError('Game does not exist')
        return value

    def validate_user(self, value):
        if not accounts_model.User.objects.filter(id=value).exists():
            raise exceptions.ValidationError('User does not exist')
        return value

    def validate(self, data):
        game_player = GamePlayer.objects.filter(game_id=data['game'], user_id=data['user'])
        if len(game_player) == 0:
            raise exceptions.ValidationError('User not a part of given game')
        data['game_player'] = game_player[0].id
        return data

class SocketGameSerializer(serializers.ModelSerializer):
    class Meta:
        model=Game
        fields='__all__'

class SocketGamePlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model=GamePlayer
        fields='__all__'