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
    with given players and decks, all disconnected, but with player_id

    Creates a websocket connection with api
    '''
    user = None
    game = None
    other_players = []
    self_player = None
    gts = None
    communicator = None

    def setUp(self, decks, player_count):
        '''
        Initializes a game, with given decks and players
        '''
        self.user = G(User)
        G(Token, user=self.user)
        self.game = G(Game, owner=self.user, decks=decks)
        self.gts = G(
            GameTableSnapshot,
            game=self.game,
            cards_on_table=f"{'1'*52*self.game.decks}{'0'*52*(3-self.game.decks)}"
        )
        self.self_player = G(GamePlayer, game=self.game,
                             user=self.user, cards='0'*156, player_id=1)
        for i in range(2, player_count+1):
            self.other_players.append(
                G(GamePlayer, game=self.game, cards='0'*156, player_id=i))

        # Communicator
        self.communicator = WebsocketCommunicator(
            application,
            f'ws/chat/{self.game.id}/',
            headers=[
                (b'cookie', bytes(f'token={self.user.auth_token}', 'utf-8'))]
        )

        return {
            'game_table_snapshot': self.gts,
            'players': self.other_players,
            'self_player': self.self_player
        }


class sTestJoinGame(InitGame):
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
            'current_set': None,
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
            assert True
        # response perfectly matches expected output
        elif len(diff.keys()) == 0:
            assert True
        else:
            print(json.dumps(json.loads(response), indent=4))  # Actual response
            print(diff)  # difference with expected response
            assert False
        await communicator.disconnect(code=1006)


class TestStartGame(InitGame):

    @pytest.mark.asyncio
    async def test_start_game(self):
        pass


class TestCallBluff(InitGame):

    @pytest.mark.asyncio
    async def test_call_bluff_success(self):
        self.setUp(2, 9)
        for player in self.other_players:
            player.disconnected = False
            player.save()

        # set game table snapshot
        GameTableSnapshot.objects.filter(id=self.gts.id).update(
            cards_on_table='101101'*26,  # random cards on table
            last_cards='1'+'0'*155,  # just one card, that doesnt belong to current set
            current_user=self.self_player,
            last_user=self.other_players[6],
            current_set=9,
        )
        self.gts = GameTableSnapshot.objects.get(id=self.gts.id)

        # set cards of last user
        self.gts.last_user.cards = '010010'*26  # complement of cards on table
        self.gts.last_user.save()

        # Time to call bluff
        connected, subprotocol = await self.communicator.connect()
        assert connected
        await self.communicator.receive_from()

        data_to_send = {
            'action': 'callBluff'
        }

        await self.communicator.send_json_to(data_to_send)
        
        #No need to evaluate channel layers here
        res = await self.communicator.receive_from()

        # Check last user has cards '1'*156
        assert GamePlayer.objects.get(id=self.gts.last_user.id).cards == '1'*156

        #Check new game table snapshot
        new_snapshot = GameTableSnapshot.objects.filter(
            game=self.game).order_by('updated_at').last()
        assert new_snapshot.cards_on_table == '0'*156
        assert new_snapshot.current_user == self.self_player
        assert new_snapshot.bluffCaller == self.self_player
        assert new_snapshot.bluffSuccessful == True
        assert new_snapshot.last_user is None
        assert new_snapshot.last_cards == '0'*156
        await self.communicator.disconnect(code=1006)
        await self.communicator.wait()