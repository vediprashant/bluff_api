from django.test import TestCase
from apps.accounts.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from ddf import G
from rest_framework.authtoken.models import Token
from django.contrib.auth.hashers import make_password


class gameCreationTest(TestCase):
    '''
    test to check create game api
    '''

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
