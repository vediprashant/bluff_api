import json
import random
import math

from django.db.models import Q, F
from django.db import transaction

from channels.generic.websocket import WebsocketConsumer

from apps.game.serializers import *
from apps.game.models import *
from asgiref.sync import async_to_sync


class ChatConsumer(WebsocketConsumer):
    game_player = None
    actions = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.actions = {
            # define your actions here
            'start': self.startGame,
            'play': self.updateCards,
            'callBluff': self.callBluff,
        }

    def connect(self):
        # if not self.scope['user'].is_authenticated():
        #     self.close()
        self.room_name = self.scope['url_route']['kwargs']['game_id']
        self.room_group_name = 'game_%s' % self.room_name
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        self.accept()
        request_data = {
            'game': self.room_name,
            'user': self.scope['user'].id
            #'user': 1  # FOR TESTING ONLY, REPLACE WITH ABOVE LINE
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

    def getNextPlayer(self):
        # minimum one player should be there in game with player_id set
        # current player is assumed to be myself
        all_players = self.game_player.game.gameplayer_set.filter(
            ~Q(player_id=None))
        # When not testing Replace above line with follwing to process only connected players
        # all_players = self.game_player.game.gameplayer_set.filter(
        #     ~Q(player_id=None) & Q(disconnected=False))

        player_count = all_players.count()
        self_id = self.game_player.player_id
        all_players = all_players.annotate(
            distance=(F('player_id')-self_id+player_count) % player_count)
        result = all_players.filter(
            ~Q(distance=0)).order_by('distance').first()
        return result

    def fromSet(self, current_set, cards):
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

    def cardsUnion(self, base_cards, new_cards):
        '''
        Returns a string containing cards from base_cards and new_cards
        '''
        my_cards = bytearray(base_cards, 'utf-8')
        for index, card in enumerate(new_cards):
            if card == '1':
                my_cards[index] = ord(card)
        return my_cards.decode('utf-8')

    def callBluff(self, data):
        # if current turn or current turn + 1
        last_snapshot = self.game_player.game.gametablesnapshot_set.order_by(
            'updated_at').last()
        # check if im current user and call bluff on last player who played
        # unless that last player is myself as well
        # update gamestate
        print(last_snapshot.currentUser)
        print(self.game_player)
        if last_snapshot.currentUser == self.game_player \
                and last_snapshot.lastUser != self.game_player:
            # Check last cards and currentset
            if self.fromSet(last_snapshot.currentSet, last_snapshot.cardsOnTable):
                # table cards are mine
                self.game_player.cards = self.cardsUnion(
                    self.game_player.cards, last_snapshot.cardsOnTable)
                currentUser=last_snapshot.lastUser #The guy whose turn is next
                loser=self.game_player# the guy who lost the bluff
            else:
                # table cards are his
                last_snapshot.lastUser.cards = self.cardsUnion(
                    last_snapshot.lastUser.cards, last_snapshot.cardsOnTable)
                currentUser = self.game_player #The guy whose turn is next
                loser = last_snapshot.lastUser # the guy who lost the bluff
            new_snapshot = GameTableSnapshot(
                game=last_snapshot.game,
                currentSet=None,
                cardsOnTable='0'*156,
                lastCards='0'*156,
                lastUser=None,
                currentUser=currentUser,
                bluffCaller=self.game_player,
                bluffSuccessful=True,
                didSkip=None,
            )
            with transaction.atomic():
                loser.save() #The guy whose turn is next
                new_snapshot.save()
        print('sending data')

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

    def updateCards(self, text_data):
        '''
        update cards on table and player cards when card is played
        '''
        print(text_data)
        cards = self.game_player.cards
        cardsOnTable = self.game_player.game.gametablesnapshot_set.latest(
            'updated_at').cardsOnTable
        print(len(cardsOnTable))
        print(len(cards))
        cardsPlayed = text_data['cardsPlayed']
        updatedCards = ""
        updatedCardsOnTable = ""
        for ele in range(len(cards)):
            if cardsPlayed[ele] == '1':
                updatedCards += '0'
                updatedCardsOnTable += '1'
            else:
                updatedCards += cards[ele]
                updatedCardsOnTable += cardsOnTable[ele]
        update_player_serializer = SocketGamePlayerSerializer(
            self.game_player, data={'cards': updatedCards}, partial=True)
        update_player_serializer.is_valid(raise_exception=True)
        update_player_serializer.save()
        print(cardsPlayed)
        print(updatedCards)
        print(updatedCardsOnTable)
        GameTableSnapshot.objects.create(
            game=self.game_player.game,
            currentSet=text_data['set'],
            cardsOnTable=updatedCardsOnTable,
            lastCards=cardsPlayed,
            lastUser=self.game_player,
            currentUser=self.game_player.game.gameplayer_set.get(
                player_id=text_data['current_user']),
            bluffCaller=None,
            bluffSuccessful=None,
            didSkip=None
        )

    def playCards(self, event):
        print(self.scope['user'])
        # self.send(text_data=json.dumps({
        #     type: "cards updated",
        #     **self.updateGameState(user_id=1)
        # }))
        self.send(text_data=json.dumps({
            'init_success': True,
            **self.updateGameState(1)
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
        if dict_data['action'] == 'play':
            print(2)
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'playCards',
                    'text': text_data,
                }
            )
