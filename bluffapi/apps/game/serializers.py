from django.db import transaction
from django.db.models import Q

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
            myself = GamePlayer.objects.create(
                user=self.context,
                game=game,
                player_id=1,
                disconnected=True,
                no_action=0,
                cards='0'*156,  # Player has no cards initially
            )
            GameTableSnapshot.objects.create(
                game=game,
                current_set=None,
                cards_on_table=self.initial_cards(game.decks), #All cards on table
                last_cards='0'*156, #no last cards
                lastUser=None,
                currentUser=myself,
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
        validated_data['cards'] = '0'*(156)
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
        game = Game.objects.filter(id=value)
        if not game.exists():
            raise exceptions.ValidationError('Game does not exist')
        return value

    def validate_user(self, value):
        if not accounts_model.User.objects.filter(id=value).exists():
            raise exceptions.ValidationError('User does not exist')
        return value

    def validate(self, data):
        game_player = GamePlayer.objects.select_related('game').filter(
            game_id=data['game'], user_id=data['user']).first()
        if game_player is None:
            raise exceptions.ValidationError('User not a part of given game')
        elif game_player.player_id is None and game_player.game.started:
            raise exceptions.ValidationError('Game already started, cannot join')
        data['game_player'] = game_player
        return data


class SocketGameSerializer(serializers.ModelSerializer):
    winner_name = serializers.SerializerMethodField()

    class Meta:
        model = Game
        fields = '__all__'

    def get_winner_name(self, obj):
        if obj.winner:
            return obj.winner.name
        return None


class GamePlayerUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = accounts_model.User
        fields = ['id', 'name', 'email']


class SocketGamePlayerSerializer(serializers.ModelSerializer):
    card_count = serializers.SerializerMethodField()
    user = GamePlayerUserSerializer()

    class Meta:
        model = GamePlayer
        fields = ['player_id', 'disconnected', 'user', 'card_count', 'cards']
        extra_kwargs = {
            'cards': {'write_only': True}
        }

    def get_card_count(self, obj):
        return obj.cards.count('1')


class SocketMyselfSerializer(serializers.ModelSerializer):
    user = GamePlayerUserSerializer()

    class Meta:
        model = GamePlayer
        fields = ['player_id', 'disconnected', 'cards', 'user']


class SocketGameTableSerializer(serializers.ModelSerializer):
    card_count = serializers.SerializerMethodField()
    current_player_id = serializers.SerializerMethodField()
    last_player_id = serializers.SerializerMethodField()
    last_card_count = serializers.SerializerMethodField()
    currentSet = serializers.SerializerMethodField()

    class Meta:
        model = GameTableSnapshot
        fields = ['currentSet', 'card_count', 'current_player_id',
                  'last_player_id', 'last_card_count']

    def get_card_count(self, obj):
        return obj.cards_on_table.count('1')

    def get_current_player_id(self, obj):
        if obj.currentUser:
            return obj.currentUser.player_id
        return None

    def get_last_player_id(self, obj):
        if obj.lastUser:
            return obj.lastUser.player_id
        return None

    def get_last_card_count(self, obj):
        if obj.last_cards:
            return obj.last_cards.count('1')
        return None

    def get_currentSet(self, obj):
        return obj.current_set


class DistributeCardsSerializer(serializers.Serializer):
    all_player_cards = serializers.DictField()

    class Meta:
        fields = ['all_player_cards']

    def create(self, validated_data):
        game = self.context['game']
        game.started = True
        last_table_snapshot = game.gametablesnapshot_set.latest('updated_at')
        with transaction.atomic():
            for player_id, cards in validated_data['all_player_cards'].items():
                player = GamePlayer.objects.get(game=game, player_id=player_id)
                player.cards = cards
                player.save()
            # Clear Game Table
            last_table_snapshot.cards_on_table = '0'*156
            last_table_snapshot.save()
            game.save()
        return game

    def validate(self, data):
        '''
        checks if each player exists
        '''
        for player_id, cards in data['all_player_cards'].items():
            # If no such game player id exists
            game = self.context['game']
            if not game.gameplayer_set\
                    .filter(player_id=player_id).exists():
                raise Exception(
                    f'player id {player_id }does not exist for this game')
            if len(cards) != 156:
                raise Exception(
                    f'Invalid cards config set for player id {player_id}')
        return data


class TimelineSerializer(serializers.Serializer):
    start_date = serializers.DateTimeField()
    end_date = serializers.DateTimeField()

    def validate(self, data):
        if data['start_date'] >= data['end_date']:
            raise serializers.ValidationError(
                'Start date cannot be later than end date')
        return data

    def to_representation(self, instance):
        super().to_representation(instance)

        all_game_players = self.context['user'].gameplayer_set.filter(
            Q(game__created_at__gt=instance['start_date']) 
            & Q(game__created_at__lt=instance['end_date'])
            & ~Q(player_id=None))
        bluff_caller_instances = GameTableSnapshot.objects.filter(
            bluffCaller__in=all_game_players
        )
        successful_bluffs = bluff_caller_instances.filter(bluffSuccessful=True)
        unsuccessful_bluffs = bluff_caller_instances.filter(bluffSuccessful=False)

        instance['successful_bluffs'] = successful_bluffs
        instance['unsuccessful_bluffs'] = unsuccessful_bluffs
        instance['all_game_players'] = all_game_players
        return instance

class InvitedPlayerSerializer(serializers.ModelSerializer):
    game_id = serializers.IntegerField() 
    email = serializers.SerializerMethodField()
    class Meta:
        model = GamePlayer
        fields = ['email', 'game_id']
        extra_kwargs = {
            'game_id': { 'write_only': True }
        }

    def validate(self, attrs):
        if not Game.objects.filter(id=attrs['game_id'], owner=self.context['user']).exists():
            raise serializers.ValidationError('User is not the owner of game')
        return attrs

    def get_email(self, obj):
        return obj.user.email
