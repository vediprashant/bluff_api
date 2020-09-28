import json
import random
import math

from django.db.models import Q

from channels.generic.websocket import WebsocketConsumer

from apps.game.serializers import *
from apps.game.models import *


class ChatConsumer(WebsocketConsumer):
    game_player = None
    actions = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.actions = {
            # define your actions here
            'start': self.startGame,
        }

    def connect(self):
        # if not self.scope['user'].is_authenticated():
        #     self.close()
        self.accept()
        request_data = {
            'game': self.scope['url_route']['kwargs']['game_id'],
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
                    ~Q(player_id=None)
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
            update_serializer = SocketGamePlayerSerializer(
                self.game_player, data=data_update, partial=True)
            update_serializer.is_valid(raise_exception=True)
            update_serializer.save()
            self.send(text_data=json.dumps({
                'init_success': True,
                **self.updateGameState(request_data['user'])
            }))
        except Exception as e:
            self.send(text_data=json.dumps({
                'init_success': False,
                'message': e.__str__()
            }))

    def disconnect(self, close_code):
        if self.game_player:
            update_serializer = SocketGamePlayerSerializer(
                self.game_player, data={'disconnected': True}, partial=True)
            update_serializer.is_valid(raise_exception=True)
            update_serializer.save()
            print('disconnect called')
            self.close()

    def updateGameState(self, user_id):
        '''
        Returns Dict containing game state
        game players in ascending order of player_id
        '''
        game = self.game_player.game
        game_players = game.gameplayer_set.order_by('player_id').filter(
            ~Q(user=user_id))  # filter() To be replaced with line below
        # filter(~Q(user=user_id) && ~Q(player_id=None))#Only return people who have joined
        myself = game.gameplayer_set.get(user=user_id)
        game_table = game.gametablesnapshot_set.latest('updated_at')
        game_state = {
            'game': SocketGameSerializer(game).data,
            'game_players': SocketGamePlayerSerializer(game_players, many=True).data,
            'self': SocketMyselfSerializer(myself).data,
            'game_table': SocketGameTableSerializer(game_table).data,
        }
        return game_state

    def startGame(self):
        '''
        start a game
        distribute cards randomly
        '''
        game_table = self.game_player.game.gametablesnapshot_set.latest(
            'updated_at')
        # List of indexes on which cards exist
        card_list = [index for index, string in enumerate(game_table.cardsOnTable)
                     if string == '1']
        total_players = self.game_player.game.gameplayer_set.filter(
            ~Q(player_id=None)
        ).order_by('player_id').last().player_id
        cards_per_player = math.floor(
            self.game_player.game.decks*52/total_players)
        all_player_cards = {}  # contains cards for each player after they are distributed

        # distribute cards from table
        for player_id in range(1, total_players+1):
            # cards of current player in loop
            my_cards = bytearray('0'*156, 'utf-8')
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

    def receive(self, text_data):
        '''
        performs specified actions
        '''
        text_data
        dict_data = json.loads(text_data)
        if not dict_data.get('action'):
            return
        # Call approriate action
        self.actions.get(
            dict_data['action'],
            lambda: self.send(text_data=json.dumps({
                'message': 'Invalid Action'
            }))
        )()
        pass
