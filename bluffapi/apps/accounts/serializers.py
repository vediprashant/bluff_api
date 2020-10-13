from rest_framework import exceptions, serializers

from django.contrib.auth.hashers import make_password

from apps.accounts import models as accounts_models


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
        if data.get('password') != data.get('confirm_password'):
            raise serializers.ValidationError('Passwords do no match')
        data.pop('confirm_password')
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
    email = serializers.EmailField()
    password = serializers.CharField(
        min_length=8
    )

    class Meta:
        fields = ['email', 'password']
