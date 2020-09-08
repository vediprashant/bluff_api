from rest_framework import exceptions, serializers

from django.contrib.auth.hashers import make_password

from apps.accounts import models as accounts_model


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer to handle signup of a user
    """
    class Meta:
        model = accounts_model.User
        fields = ('id', 'name', 'email', 'password')
        extra_kwargs = {'password': {'write_only': True, 'min_length': 8},
                        }

    def create(self, validated_data):
        if validated_data.get('password'):
            validated_data['password'] = make_password(
                validated_data['password'])
        return super(RegisterSerializer, self).create(validated_data)


class UserSerializer(serializers.ModelSerializer):
    """
    It handles all the get request
    """
    class Meta:
        model = accounts_model.User
        fields = ['name', 'email']
