import json
from channels.generic.websocket import WebsocketConsumer
from apps.game.serializers import *
from apps.game.models import *
from django.db.models import Q


class ChatConsumer(WebsocketConsumer):
    # @channel_session_user_from_http
    game = None
    game_player = None

    def connect(self):
        self.accept()
        print(self.scope['user'])
        text_data_json = {
            'game': self.scope['url_route']['kwargs']['game_id'],
            'user': self.scope['user'].id
        }

        # Initialize self variables, send game state
        serializer = SocketInitSerializer(data=text_data_json)
        try:
            serializer.is_valid(raise_exception=True)
            self.game = serializer.validated_data['game']
            self.game_player = serializer.validated_data['game_player']
            self.send(text_data=json.dumps({
                'init_success': True,
                'game_player': self.game_player,
                **self.updateGameState(text_data_json['user'])
            }))
        except Exception as e:
            self.send(text_data=json.dumps({
                'init_success': False,
                'message': e.__str__()
            }))

    def disconnect(self, close_code):
        pass

    def updateGameState(self, user_id):
        '''
        Returns Dict containing game state
        '''
        game = Game.objects.get(id=self.game)
        game_players = game.gameplayer_set.filter(~Q(user=user_id))  # To be replaced with line below
        # game.game_player_set.filter(~Q(user=user_id) && ~Q(player_id=None))#Only return people who have joined
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
        # action from user
        # update game state

        # message = text_data_json['message']
        # self.send(text_data=json.dumps({
        #     'message': message
        # }))
        pass
