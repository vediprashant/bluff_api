import json
import random
import math

from django.db.models import Q, F
from django.db import transaction

from channels.generic.websocket import WebsocketConsumer

from apps.game.serializers import *
from apps.game.models import *
from asgiref.sync import async_to_sync
from apps.game import constants as game_constants


class GameConsumer(WebsocketConsumer):
    '''
    It calles desired function whenever an event happens
    '''
    game_player = None
    actions = None

    def __init__(self, *args, **kwargs):
        '''calls functions to run based on the actions it get'''
        super().__init__(*args, **kwargs)
        self.actions = {
            # define your actions here
            'start': self.start_game,
            'play': self.update_cards,
            'callBluff': self.call_bluff,
            'skip': self.skip,
        }

    def connect(self):
        '''
        initializes gamplayer instance, sends gameState
        and connects you to the game
        '''
        if not self.scope['user'].is_authenticated():
            self.close()
            return
        self.room_name = self.scope['url_route']['kwargs']['game_id']
        self.room_group_name = f'game_{self.room_name}'
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        self.accept()
        request_data = {
            'game': self.room_name,
            'user': self.scope['user'].id
            # 'user': 1  # FOR TESTING ONLY, REPLACE WITH ABOVE LINE
        }
        # Initialize self variables,update gameplayer , send game state
        serializer = SocketInitSerializer(data=request_data)
        try:
            serializer.is_valid(raise_exception=True)
            self.game_player = serializer.validated_data['game_player']
            # assign a player_id, set disconnected to false
            if self.game_player.player_id is None:
                last_player = self.game_player.game.gameplayer_set.filter(
                    player_id__isnull=False
                ).order_by('player_id').last()
                # If no one has been assigned any player_id, last_player is none
                if last_player:
                    last_player_id = last_player.player_id
                else:
                    last_player_id = 0
                if last_player_id >= 9:
                    raise Exception('Game is Full')
                data_update = {
                    'disconnected': False,
                    'player_id': last_player_id+1
                }

            else:
                data_update = {
                    'disconnected': False
                }
            connected_players = GamePlayer.objects.filter(
                game=self.game_player.game, disconnected=False)
            if not connected_players.exists():
                # check if game is started
                game = Game.objects.get(id=self.game_player.game.id)
                if game.started and game.winner is None:
                    last_snapshot = GameTableSnapshot.objects.filter(
                        game=self.game_player.game).latest('updated_at')
                    last_snapshot.current_user = self.game_player
                    last_snapshot.save()

            update_serializer = SocketGamePlayerSerializer(
                self.game_player, data=data_update, partial=True)
            update_serializer.is_valid(raise_exception=True)
            update_serializer.save()
            self.send(text_data=json.dumps({
                'init_success': True,
                **self.update_game_state(request_data['user'])
            }))
        except Exception as e:
            self.send(text_data=json.dumps({
                'init_success': False,
                'message': e.__str__()
            }))
            self.close()
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'play_cards'
            }
        )

    def disconnect(self, close_code):
        '''
        Skips turn if its players turn ans game is started and runs 
        Clean up code when user disconnects
        '''
        if self.game_player:
            self.game_player = GamePlayer.objects.\
                select_related('game').get(id=self.game_player.id)
            # Check if he was current user
            last_snapshot = GameTableSnapshot.objects.filter(
                game=self.game_player.game).latest('updated_at')
            if last_snapshot.current_user == self.game_player \
                    and self.game_player.game.started:
                # Make him skip his turn
                self.skip('Forced Skip')
            update_serializer = SocketGamePlayerSerializer(
                self.game_player, data={'disconnected': True}, partial=True)
            update_serializer.is_valid(raise_exception=True)
            update_serializer.save()
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'play_cards'
                }
            )
            self.close()

    def update_game_state(self, user_id):
        '''
        Returns object conatining game_state having details 
        of game,players,self and table
        '''
        game = Game.objects.prefetch_related(
            'gameplayer_set').get(id=self.game_player.game.id)
        game_players = game.gameplayer_set.order_by('player_id').filter(
            ~Q(user=user_id) & Q(player_id__isnull=False))  # filter() To be replaced with line below
        # filter(~Q(user=user_id) && Q(player_id__isnull=False))#Only return people who have joined
        myself = game.gameplayer_set.get(user=user_id)
        game_table = game.gametablesnapshot_set.latest('updated_at')
        game_state = {
            'game': SocketGameSerializer(game).data,
            'game_players': SocketGamePlayerSerializer(game_players, many=True).data,
            'self': SocketMyselfSerializer(myself).data,
            'game_table': SocketGameTableSerializer(game_table).data,
        }
        return game_state

    def get_next_player(self, showAll=False):
        '''
        Default: returns next connected player in player circle
        showAll = True : returns next player in player circle
        '''
        # minimum one player should be there in game with player_id set
        # current player is assumed to be myself
        all_players = GamePlayer.objects.filter(
            Q(player_id__isnull=False) & Q(game=self.game_player.game))
        # When not testing Replace above line with follwing to process only connected players
        # all_players = self.game_player.game.gameplayer_set.filter(
        #     ~Q(player_id=None) & Q(disconnected=False))

        player_count = all_players.count()
        self_id = self.game_player.player_id
        all_players = all_players.annotate(
            distance=(F('player_id')-self_id+player_count) % player_count)
        if showAll:
            result = all_players.filter(
                ~Q(distance=0)).order_by('distance').first()
        else:
            result = all_players.filter(
                ~Q(distance=0) & Q(disconnected=False)).order_by('distance').first()
        return result

    def is_it_my_turn(self):
        '''Checks if it's turn of current user
        '''
        current_snapshot = GameTableSnapshot.objects.filter(
            game=self.game_player.game).order_by('updated_at').last()
        if current_snapshot.current_user and current_snapshot.current_user.disconnected == True:
            if self.game_player == self.get_next_player():
                return True
        elif current_snapshot.current_user == self.game_player:
            return True
        return False

    def from_set(self, current_set, cards):
        '''
        Whether all cards belong to given set
        '''
        # Assumes current_set between 1 and 13
        # List of indexes on which cards exist
        card_list = [index for index, string in enumerate(cards)
                     if string == '1']
        for card in card_list:
            if math.ceil((card+1)/12) != current_set:
                return False
        return True

    def cards_union(self, base_cards, new_cards):
        '''
        Returns a string containing cards from base_cards and new_cards
        '''
        my_cards = bytearray(base_cards, 'utf-8')
        for index, card in enumerate(new_cards):
            if card == '1':
                my_cards[index] = ord(card)
        return my_cards.decode('utf-8')

    def call_bluff(self, data):
        '''
        Performs Call Bluff Operation if either i'm current player
        or i'm next player
        '''
        # if current turn or current turn + 1
        self.game_player = GamePlayer.objects.get(id=self.game_player.id)
        last_snapshot = GameTableSnapshot.objects.filter(
            game=self.game_player.game).latest('updated_at')
        # check if im current user and call bluff on last player who played
        # unless that last player is myself as well
        # update gamestate
        if (last_snapshot.current_user == self.game_player
            or self.get_next_player == self.game_player) \
                and last_snapshot.last_user != self.game_player:
            # Check last cards and current_set
            if self.from_set(last_snapshot.current_set, last_snapshot.last_cards):
                # table cards are mine
                self.game_player.cards = self.cards_union(
                    self.game_player.cards, last_snapshot.cards_on_table)
                current_user = last_snapshot.last_user  # The guy whose turn is next
                loser = self.game_player  # the guy who lost the bluff
                # Check if He has no cards left
            else:
                # table cards are his
                last_snapshot.last_user.cards = self.cards_union(
                    last_snapshot.last_user.cards, last_snapshot.cards_on_table)
                current_user = self.game_player  # The guy whose turn is next
                loser = last_snapshot.last_user  # the guy who lost the bluff
            if last_snapshot.last_user.cards == '0'*game_constants.MAX_CARD_LENGTH:
                # He is the winner
                current_user = None
                Game.objects.filter(id=self.game_player.game.id).update(
                    winner=last_snapshot.last_user.user)
            new_snapshot = GameTableSnapshot(
                game=last_snapshot.game,
                current_set=None,
                cards_on_table='0'*game_constants.MAX_CARD_LENGTH,
                last_cards='0'*game_constants.MAX_CARD_LENGTH,
                last_user=None,
                current_user=current_user,
                bluff_caller=self.game_player,
                bluff_successful=True,
                did_skip=None,
            )
            with transaction.atomic():
                loser.save()  # The guy whose turn is next
                new_snapshot.save()
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'play_cards',
                'text': 'asdfasd',
                'bluff_cards': last_snapshot.last_cards,
                'action': 'Show',
                'bluffLooser': loser.user.name,
                'last_player_turn': self.game_player.player_id
            }
        )

    def skip(self, data):
        '''It skips turn of the user'''
        self.game_player = GamePlayer.objects.get(id=self.game_player.id)
        if not self.is_it_my_turn():
            return
        current_snapshot = GameTableSnapshot.objects.filter(
            game=self.game_player.game).latest('updated_at')
        current_snapshot.did_skip = True
        # Check if next player(connected or not) has no cards left
        next_joined_player = self.get_next_player(showAll=True)

        # Logic to empty the table and start next round
        # If i'm the last user who played cards
        if current_snapshot.last_user == self.game_player:
            # Empty the table, i begin the next round
            next_snapshot_data = {
                'cards_on_table': '0'*game_constants.MAX_CARD_LENGTH,
                'current_user': self.game_player,
                'last_user': None,
                'current_set': None,
                'last_cards': '0'*game_constants.MAX_CARD_LENGTH,
            }
        else:  # Whoever is next
            next_snapshot_data = {
                'cards_on_table': current_snapshot.cards_on_table,
                'current_user': self.get_next_player(),
                'last_user': current_snapshot.last_user,
                'last_cards': current_snapshot.last_cards,
                'current_set': current_snapshot.current_set,
            }

        with transaction.atomic():
            current_snapshot.save()
            if self.game_player.game.started == True and next_joined_player.cards == '0'*game_constants.MAX_CARD_LENGTH:
                # next player is winner
                Game.objects.filter(id=self.game_player.game.id).update(
                    winner=next_joined_player.user)
                next_snapshot_data['current_user'] = None
            new_snapshot = GameTableSnapshot(
                game=self.game_player.game,
                bluff_caller=None,
                bluff_successful=None,
                did_skip=None,
                **next_snapshot_data
            ).save()

        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'play_cards',
                'text': 'sdfasdfasd',
                'action': 'skip',
                'last_player_turn': self.game_player.player_id
            }
        )

    def start_game(self, text_data):
        '''
        start a game
        distribute cards randomly
        '''
        self.game_player = GamePlayer.objects.get(id=self.game_player.id)
        game_table = self.game_player.game.gametablesnapshot_set.latest(
            'updated_at')
        # List of indexes on which cards exist
        card_list = [index for index, string in enumerate(game_table.cards_on_table)
                     if string == '1']
        total_players = self.game_player.game.gameplayer_set.filter(
            Q(player_id__isnull=False)
        ).order_by('player_id').last().player_id
        cards_per_player = math.floor(
            self.game_player.game.decks*52/total_players)
        all_player_cards = {}  # contains cards for each player after they are distributed

        # distribute cards from table
        for player_id in range(1, total_players+1):
            # cards of current player in loop
            my_cards = bytearray('0'*game_constants.MAX_CARD_LENGTH, 'utf-8')
            # Get Random cards from table
            for i in range(cards_per_player):
                acquired_card = random.randint(0, len(card_list)-1)
                my_cards[card_list[acquired_card]] = ord(
                    '1')  # Add card to my cards
                card_list.pop(acquired_card)  # Remove card from card list
            all_player_cards[player_id] = my_cards.decode('utf-8')
        distribute_serializer = DistributeCardsSerializer(
            data={'all_player_cards': all_player_cards},
            context={'game': self.game_player.game}
        )
        distribute_serializer.is_valid()
        distribute_serializer.save()
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'play_cards',
                'text': 'sdfasdfasd',
            }
        )

    def update_cards(self, text_data):
        '''
        update cards on table and player cards when card is played
        '''
        if not self.is_it_my_turn():
            return
        self.game_player = GamePlayer.objects.get(id=self.game_player.id)
        cards = self.game_player.cards
        game_table = self.game_player.game.gametablesnapshot_set.latest(
            'updated_at')
        cards_on_table = game_table.cards_on_table
        next_user = self.get_next_player()
        if game_table.last_user is not None and game_table.last_user.cards == '0'*game_constants.MAX_CARD_LENGTH:
            # He is the winner
            next_user = None
            Game.objects.filter(id=self.game_player.game.id).update(
                winner=game_table.last_user.user)
        cards_played = text_data['cardsPlayed']
        updated_cards = ""
        updated_cards_on_table = ""
        played_card_count = 0
        for ele in range(len(cards)):
            if cards_played[ele] == '1':
                updated_cards += '0'
                updated_cards_on_table += '1'
                played_card_count += 1
            else:
                updated_cards += cards[ele]
                updated_cards_on_table += cards_on_table[ele]
        update_player_serializer = SocketGamePlayerSerializer(
            self.game_player, data={'cards': updated_cards}, partial=True)
        update_player_serializer.is_valid(raise_exception=True)
        update_player_serializer.save()
        GameTableSnapshot.objects.create(
            game=self.game_player.game,
            current_set=text_data['set'],
            cards_on_table=updated_cards_on_table,
            last_cards=cards_played,
            last_user=self.game_player,
            current_user=next_user,
            bluff_caller=None,
            bluff_successful=None,
            did_skip=None
        )
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'play_cards',
                'text': text_data,
                'action': f"played {played_card_count} card",
                'last_player_turn': self.game_player.player_id,
            }
        )

    def play_cards(self, event):
        '''send data of the game to webSockets'''
        self.send(text_data=json.dumps({
            **self.update_game_state(self.scope['user'].id),
            'bluff_cards': event.get('bluff_cards'),
            'action': event.get('action'),
            'last_player_turn': event.get('last_player_turn'),
            'bluffLooser': event.get('bluffLooser'),
        }))

    def receive(self, text_data):
        '''
        performs specified actions
        '''
        dict_data = json.loads(text_data)
        if not dict_data.get('action'):
            return
        # Call approriate action
        self.actions.get(
            dict_data['action'],
            lambda: self.send(text_data=json.dumps({
                'message': 'Invalid Action'
            }))
        )(dict_data)
