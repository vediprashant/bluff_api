from django.db.models import Q
from django.db import transaction, IntegrityError

from rest_framework import serializers, exceptions

from apps.game.models import Game, GamePlayer, GameTableSnapshot
from apps.accounts import models as accounts_model
from apps.game import constants as game_constants


class CreateGameSerializer(serializers.ModelSerializer):
    '''
    validates 3 >= decks >= 1
    creates a game
    '''
    decks = serializers.IntegerField(
        max_value=3,
        min_value=1
    )

    class Meta:
        model = Game
        fields = ['decks', 'id']
        extra_kwargs = {
            'decks': {'write_only': True}
        }

    def initial_cards(self, decks):
        ''' Initializes cards based on the decks'''
        max_decks = int(game_constants.MAX_CARD_LENGTH/52)
        return f"{'1'*decks}{'0'*(max_decks-decks)}"*52

    def create(self, validated_data):
        '''
        Creates instance of game, gamePlayer instance of the owner
        and initializes table
        '''
        with transaction.atomic():
            game = Game.objects.create(
                started=False,
                owner=self.context['request'].user,
                winner=None,
                decks=validated_data['decks']
            )
            myself = GamePlayer.objects.create(
                user=self.context['request'].user,
                game=game,
                player_id=1,
                disconnected=True,
                no_action=0,
                cards='0'*game_constants.MAX_CARD_LENGTH,  # Player has no cards initially
            )
            GameTableSnapshot.objects.create(
                game=game,
                current_rank=None,
                cards_on_table=self.initial_cards(
                    game.decks),  # All cards on table
                last_cards='0'*game_constants.MAX_CARD_LENGTH,  # no last cards
                last_user=None,
                current_user=myself,
                bluff_caller=None,
                bluff_successful=None,
                did_skip=None
            )
        return game


class CreateGamePlayerSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        queryset=accounts_model.User.objects.all(), slug_field='email')

    class Meta:
        model = GamePlayer
        fields = ['game', 'user']

    def validate(self, data):
        if data['game'].owner != self.context['request'].user:
            raise serializers.ValidationError('User is not the owner of game')
        return super().validate(data)


class GameSerializer(serializers.ModelSerializer):
    '''
    Serializer to return list of games
    '''
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
        '''
        check if the user exists
        '''
        if not accounts_model.User.objects.filter(id=value).exists():
            raise exceptions.ValidationError('User does not exist')
        return value

    def validate(self, data):
        '''
        validates if the users is part of the game and game is not started yet
        '''
        game_player = GamePlayer.objects.select_related('game').filter(
            game_id=data['game'], user_id=data['user']).first()
        if game_player is None:
            raise exceptions.ValidationError('User not a part of given game')
        elif game_player.player_id is None and game_player.game.started:
            raise exceptions.ValidationError(
                'Game already started, cannot join')
        data['game_player'] = game_player
        return data


class SocketGameSerializer(serializers.ModelSerializer):
    '''
    Returns all the fields of the Game and name of the winner
    '''
    winner_name = serializers.CharField(source='winner.name', default=None)

    class Meta:
        model = Game
        fields = ['started', 'winner', 'owner', 'winner_name']


class GamePlayerUserSerializer(serializers.ModelSerializer):
    '''
    Serializers to get the details of the player from User model
    '''
    class Meta:
        model = accounts_model.User
        fields = ['id', 'name', 'email']


class SocketGamePlayerSerializer(serializers.ModelSerializer):
    '''
    Serializer to handle properties of other gamePlayers
    '''
    card_count = serializers.SerializerMethodField()
    user = GamePlayerUserSerializer()

    class Meta:
        model = GamePlayer
        fields = ['player_id', 'disconnected', 'user', 'card_count', 'cards']
        extra_kwargs = {
            'cards': {'write_only': True}
        }

    def get_card_count(self, obj):
        '''Returns count of the cards present from cards field'''
        return obj.cards.count('1')


class SocketMyselfSerializer(serializers.ModelSerializer):
    '''
    Serializer to handle properties of current gamePlayer
    '''
    user = GamePlayerUserSerializer()

    class Meta:
        model = GamePlayer
        fields = ['player_id', 'disconnected', 'cards', 'user']


class SocketGameTableSerializer(serializers.ModelSerializer):
    '''
    Serializer for gameTableSnapshot to send modified fields of it
    '''
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
        '''returns count of cards_on_table'''
        return obj.cards_on_table.count('1')

    def get_current_player_id(self, obj):
        return obj.current_user.player_id if obj.current_user else None

    def get_last_player_id(self, obj):
        return obj.last_user.player_id if obj.last_user else None

    def get_last_card_count(self, obj):
        '''returns count of last_cards_played'''
        return obj.last_cards.count('1') if obj.last_cards else None

    def get_currentSet(self, obj):
        return obj.current_rank


class DistributeCardsSerializer(serializers.Serializer):
    '''
    It Distributes Cards among all players and save their cards
    '''
    all_player_cards = serializers.DictField()

    class Meta:
        fields = ['all_player_cards']

    def create(self, validated_data):
        '''It updates cards,starts game and updates gameTable'''
        game = self.context['game']
        game.started = True
        last_table_snapshot = game.gametablesnapshot_set.latest('updated_at')
        with transaction.atomic():
            for player_id, cards in validated_data['all_player_cards'].items():
                player = GamePlayer.objects.get(game=game, player_id=player_id)
                player.cards = cards
                player.save()
            # Clear Game Table
            last_table_snapshot.cards_on_table = '0'*game_constants.MAX_CARD_LENGTH
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
                    f'player id {player_id} does not exist for this game')
            if len(cards) != game_constants.MAX_CARD_LENGTH:
                raise Exception(
                    f'Invalid cards config set for player id {player_id}')
        return data

# Intended for stats part of project.
# WIP, No review fixes done here yet


class TimelineSerializer(serializers.Serializer):
    '''
    It takes start_date and end_date and sends details of bluff 
    from all games in that time period
    '''
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
            & Q(player_id__isnull=False))
        bluff_caller_instances = GameTableSnapshot.objects.filter(
            bluff_caller__in=all_game_players
        )
        successful_bluffs = bluff_caller_instances.filter(
            bluff_successful=True)
        unsuccessful_bluffs = bluff_caller_instances.filter(
            bluff_successful=False)

        instance['successful_bluffs'] = successful_bluffs
        instance['unsuccessful_bluffs'] = unsuccessful_bluffs
        instance['all_game_players'] = all_game_players
        return instance


class InvitedPlayerSerializer(serializers.ModelSerializer):
    '''
    Serializer to send invitedPlayers of a game
    '''
    email = serializers.EmailField(source='user.email')

    class Meta:
        model = GamePlayer
        fields = ['email', 'game_id']


class GameStatsSerializer(serializers.ModelSerializer):
    '''
    Serializer to handle properties of other gamePlayers
    '''
    user = GamePlayerUserSerializer()
    game = SocketGameSerializer()
    card_count = serializers.SerializerMethodField()
    owner = serializers.SerializerMethodField()

    class Meta:
        model = GamePlayer
        fields = ['owner']

    def get_card_count(self, obj):
        '''Returns count of the cards present from cards field'''
        return obj.cards.count('1')

    def get_owner(self, obj):
        '''Returns if current user is the owner of game'''
        return obj.game.owner == self.context['request'].user
