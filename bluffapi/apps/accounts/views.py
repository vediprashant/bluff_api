from django.contrib.auth import authenticate

from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework import status

from apps.accounts import (
    models as accounts_models, serializers as accounts_serializers
)
from apps.accounts.serializers import LoginSerializer


class UserViewSet(viewsets.ModelViewSet):
    """
    View to handle all the request to user
    """
    queryset = accounts_models.User.objects.all()

    # Redirect towards the required serializer based on request
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return accounts_serializers.RegisterSerializer
        else:
            return accounts_serializers.UserSerializer

class Login(APIView):
    def post(self, request):
        data = {
            'username': request.POST['email'],
            'password': request.POST['password']
        }
        loginSerializer = LoginSerializer(data=data)
        loginSerializer.is_valid(raise_exception=True)
        user = authenticate(request, **loginSerializer.validated_data)
        if user is not None:
            token, created = Token.objects.get_or_create(user=user)
            return Response({ 'token': token.key })
        else:
            return Response({ 'message': 'Invalid Credentials'},
                            status=status.HTTP_401_UNAUTHORIZED)
