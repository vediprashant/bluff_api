from django.test import TestCase
from apps.accounts.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from ddf import G
from rest_framework.authtoken.models import Token
from django.contrib.auth.hashers import make_password


class UserTest(TestCase):

    def test_User_Created(self):
        '''
        user should be created when data provided is good
        '''
        input_dict = {
            'name': 'Naveen',
            'email': 'a@b.com',
            'password': 'a12345678',
        }
        response = self.client.post(
            reverse('user-list'),
            input_dict
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_bad_email(self):
        '''
        tests invalid email format
        '''
        response = self.client.post(
            reverse('user-list'),
            {
                'name': 'Naveen',
                'email': 'ab.com',  # Email without @
                'password': 'a12345678',
            }
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_no_name(self):
        '''
        tests when no name is provided
        '''
        response = self.client.post(
            reverse('user-list'),
            {  # No Name
                'email': 'a@b.com',
                'password': 'a12345678',
            }
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_short(self):
        '''
        tests when password length is shorter<8
        '''
        response = self.client.post(
            reverse('user-list'),
            {
                'name': 'naveen',
                'email': 'a@b.com',
                'password': 'a123456',  # password <8 characters
            }
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_email_exists(self):
        '''
        tests when a user with same email already exists
        '''
        G(User, email='a@b.com')
        response = self.client.post(
            reverse('user-list'),
            {
                'name': 'naveen',
                'email': 'a@b.com',
                'password': 'a12345678',
            }
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginTest(TestCase):
    def test_returns_token(self):
        user = G(User, email='a@b.com', password=make_password('a12345678'))
        token = G(Token, user=user)
        response = self.client.post(
            reverse('login'),
            {
                'email': 'a@b.com',
                'password': 'a12345678',
            }
        )
        self.assertEqual(response.data['token'], token.key)

    def test_wrong_pass(self):
        G(User, email='a@b.com', password=make_password('a12345678'))
        response = self.client.post(
            reverse('login'),
            {
                'email': 'a@b.com',
                'password': 'a1234567',  # diff password
            }
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_wrong_email_format(self):
        G(User, email='a@b.com', password=make_password('a12345678'))
        response = self.client.post(
            reverse('login'),
            {
                'email': 'ab.com',  # incorrect email format
                'password': 'a12345678',
            }
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LogoutTest(TestCase):
    """
    Test To check functioning of logout api
    """
    # When credentials are correct

    def test_sucessful_logout(self):
        user = G(User, email='a@b.com', password=make_password('a12345678'))
        token = G(Token, user=user)
        auth_headers = {
            'HTTP_AUTHORIZATION': 'Token ' + token.key,
        }
        response = self.client.post(reverse('logout'), **auth_headers)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    # when unauthenticated user tries to logout
    def test_unauthenticated_logout(self):
        response = self.client.post(reverse('logout'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # when token provided is not correct
    def test_invalid_token(self):
        auth_headers = {
            'HTTP_AUTHORIZATION': 'Token ' + 'qwerty11',
        }
        response = self.client.post(reverse('logout'), **auth_headers)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
