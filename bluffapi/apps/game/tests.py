import json
import pprint
from deepdiff import DeepDiff

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.hashers import make_password

from rest_framework import status
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from ddf import G
import pytest
from channels.testing import WebsocketCommunicator

from apps.accounts.models import User
from apps.game.consumers import ChatConsumer
from apps.game.models import *
from bluffapi.routing import application
from apps.game.serializers import *


class gameCreationTest(TestCase):
    """
    test to check create game api
    """

    def test_unauthenticated_user(self):
        response = self.client.post(reverse('create_game'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_token(self):
        auth_headers = {
            'HTTP_AUTHORIZATION': 'Token ' + 'qwerty11',
        }
        response = self.client.post(reverse('create_game'), **auth_headers)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_successful_game_creation(self):
        user = G(User, email='a@b.com', password=make_password('a12345678'))
        token = G(Token, user=user)
        self.client.defaults['HTTP_AUTHORIZATION'] = 'Token ' + token.key
        response = self.client.post(reverse('create_game'), {
                                    'decks': '1'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_decks(self):
        user = G(User, email='a@b.com', password=make_password('a12345678'))
        token = G(Token, user=user)
        self.client.defaults['HTTP_AUTHORIZATION'] = 'Token ' + token.key
        response = self.client.post(reverse('create_game'), {
                                    'decks': 4})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


@pytest.mark.django_db(transaction=True)
class InitGame:
    '''
    Base class for socket based modules, initializes a game
    '''
    user = None
    game = None

    def setUp(self, decks, player_count):
        '''
        Initializes a game, with given decks and players
        '''
        self.user = G(User)
        G(Token, user=self.user)
        self.game = G(Game, owner=self.user, decks=decks)
        gts = G(
            GameTableSnapshot,
            game=self.game,
            cardsOnTable=f"{'1'*52*self.game.decks}{'0'*52*(3-self.game.decks)}"
        )
        self_player = G(GamePlayer, game=self.game,
                        user=self.user, cards='0'*156 , player_id=1)
        other_players = []
        for i in range(2, player_count+1):
            other_players.append(
                G(GamePlayer, game=self.game, cards='0'*156, player_id=i))
        return {
            'game_table_snapshot': gts,
            'players': other_players,
            'self_player': self_player
        }


class TestJoinGame(InitGame):
    '''
    Tests "game join" and "game start"
    '''
    expected_response = None

    def generate_expected_response(self, gts, players):
        '''
        Generates a useful/relevant subset of expected response
        '''
        output_dict = {}
        output_dict['game_players'] = []
        for player in players:
            output_dict['game_players'].append({
                'card_count': 0,
                'disconnected': player.disconnected,
                'player_id': player.player_id,
                'user': {
                    'email': player.user.email,
                    'id': player.user.id,
                    'name': player.user.name
                }
            })
        output_dict['init_success'] = True
        output_dict['game_table'] = {
            'currentSet': None,
            'card_count': self.game.decks*52
        }
        output_dict['self'] = {
            'disconnected': False,
            'cards': '0'*156
        }
        self.expected_response = output_dict

    @pytest.mark.asyncio
    async def test_game_join(self):
        '''
        Test for joining a game
        '''
        init_game = self.setUp(0, 9)
        self.generate_expected_response(
            gts=init_game['game_table_snapshot'],
            players=init_game['players']
        )
        communicator = WebsocketCommunicator(
            application,
            f'ws/chat/{self.game.id}/',
            headers=[
                (b'cookie', bytes(f'token={self.user.auth_token}', 'utf-8'))]
        )
        connected, subprotocol = await communicator.connect()
        response = await communicator.receive_from()
        diff = DeepDiff(json.loads(response), self.expected_response,
                        ignore_order=True)
        # response contains extra stuff and nothing more
        if diff.get('dictionary_item_removed') and len(diff.keys()) == 1:
            assert False
        # response perfectly matches expected output
        elif len(diff.keys()) == 0:
            assert True
        else:
            print(json.dumps(json.loads(response), indent=4))  # Actual response
            print(diff)  # difference with expected response
            assert False


class TestStartGame(InitGame):

    @pytest.mark.asyncio
    async def test_start_game(self):
        pass
