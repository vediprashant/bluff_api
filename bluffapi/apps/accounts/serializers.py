from rest_framework import exceptions, serializers

from django.contrib.auth.hashers import make_password

from apps.accounts import models as accounts_models
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from django.contrib.auth import authenticate


class RegisterSerializer(serializers.ModelSerializer):
    '''
    Serializer to handle signup of a user
    '''
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = accounts_models.User
        fields = ('id', 'name', 'email', 'password', 'confirm_password')
        extra_kwargs = {'password': {'write_only': True, 'min_length': 8},
                        }

    def validate(self, data):
        super(RegisterSerializer, self).validate(data)
        confirm_password = data.pop('confirm_password')
        if data['password'] != confirm_password:
            raise serializers.ValidationError('Passwords do no match')
        return data

    def create(self, validated_data):
        validated_data['password'] = make_password(
            validated_data['password'])
        return super(RegisterSerializer, self).create(validated_data)


class UserSerializer(serializers.ModelSerializer):
    '''
    Serializer to show user details of a user
    '''
    class Meta:
        model = accounts_models.User
        fields = ['name', 'email']


class LoginSerializer(serializers.Serializer):
    '''
    Validates Email and Password format for login
    '''
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(
        min_length=8, write_only=True
    )
    token = serializers.CharField(read_only=True)

    class Meta:
        fields = ['email', 'password']

    def create(self, validated_data):
        user = authenticate(**validated_data)
        if user is None:
            raise serializers.ValidationError('Invalid Credentials')
        token, created = Token.objects.get_or_create(user=user)
        validated_data['token'] = token.key
        return validated_data
