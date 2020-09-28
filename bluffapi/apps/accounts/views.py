from django.contrib.auth import authenticate

from rest_framework import viewsets, permissions
from rest_framework.generics import CreateAPIView
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
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


class Login(CreateAPIView):
    def post(self, request):
        loginSerializer = LoginSerializer(data=request.data)
        loginSerializer.is_valid(raise_exception=True)
        user = authenticate(request, **loginSerializer.validated_data)
        if user is not None:
            token, created = Token.objects.get_or_create(user=user)
            return Response(
                {'token': token.key})
        else:
            return Response({
                'message': 'Invalid Credentials'},
                status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(CreateAPIView):
    """
    It deletes the token and logout user
    """
    authentication_classes = (TokenAuthentication, )
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        token_object = Token.objects.filter(user=request.user)
        token_object.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
