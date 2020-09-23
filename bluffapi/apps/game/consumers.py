import json
from channels.generic.websocket import WebsocketConsumer
from apps.game.serializers import *
from apps.game.models import *
from django.db.models import Q


class ChatConsumer(WebsocketConsumer):
    game_player = None

    def connect(self):
        # if not self.scope['user'].is_authenticated():
        #     self.close()
        self.accept()
        print(self.scope['user'])
        request_data = {
            'game': self.scope['url_route']['kwargs']['game_id'],
            # 'user': self.scope['user'].id
            'user': 1  # FOR TESTING ONLY, REPLACE WITH ABOVE LINE
        }

        # Initialize self variables,update gameplayer , send game state
        serializer = SocketInitSerializer(data=request_data)
        try:
            serializer.is_valid(raise_exception=True)
            # print(self.game_player)
            self.game_player = serializer.validated_data['game_player']

            if self.game_player.player_id is None:
                last_player_id = self.game_player.game.gameplayer_set.filter(
                    ~Q(player_id=None)
                ).order_by('player_id').last().player_id
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
                self.game_player, data={'disconnected':True}, partial=True)
            update_serializer.is_valid(raise_exception=True)
            update_serializer.save()

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

    def receive(self, text_data):
        print(text_data)
        pass
