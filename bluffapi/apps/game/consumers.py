import json
from channels.generic.websocket import WebsocketConsumer
from apps.game.serializers import *
from apps.game.models import *
from django.db.models import Q

class ChatConsumer(WebsocketConsumer):
    #@channel_session_user_from_http
    game = None
    game_player = None

    def connect(self):
        self.accept()

    def disconnect(self, close_code):
        pass

    def updateGameState(self):
        '''
        Returns Dict containing game state
        '''
        game = Game.objects.get(id=self.game)
        game_players = game.gameplayer_set.all() #To be replaced with line below
        #game.game_player_set.filter(~Q(player_id=None))#Only return people who have joined
        game_state = {
            'game': SocketGameSerializer(game).data,
            'game_players': SocketGamePlayerSerializer(game_players, many=True).data
        }
        return game_state

    def receive(self, text_data):
        # action from user
        # update game state
        text_data_json = json.loads(text_data)

        if not (self.game and self.game_player):
            #Initialize self variables, send game state
            serializer = SocketInitSerializer(data=text_data_json)
            try:
                serializer.is_valid(raise_exception=True)
                self.game = serializer.validated_data['game']
                self.game_player = serializer.validated_data['game_player']
                self.send(text_data=json.dumps({
                    'init_success': True,
                    'game_player': self.game_player,
                    **self.updateGameState()
                }))
            except Exception as e:
                self.send(text_data=json.dumps({
                    'init_success': False,
                    'message': e.__str__()
                }))
        else:
            print('nahh')
        #message = text_data_json['message']
        # self.send(text_data=json.dumps({
        #     'message': message
        # }))
