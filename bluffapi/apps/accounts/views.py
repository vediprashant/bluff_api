from django.contrib.auth import authenticate

from rest_framework import viewsets, permissions
from rest_framework.generics import CreateAPIView, DestroyAPIView
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import send_mail
from django.conf import settings
from apps.accounts.tasks import send_signup_mail

from apps.accounts import (
    models as accounts_models, serializers as accounts_serializers,
    constants as accounts_constants
)

from apps.accounts.serializers import LoginSerializer


class UserViewSet(viewsets.ModelViewSet):
    '''
    View to handle all the request to user
    '''
    queryset = accounts_models.User.objects.all()

    # Redirect towards the required serializer based on request
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return accounts_serializers.RegisterSerializer
        else:
            return accounts_serializers.UserSerializer

    def create(self, request):
        response = super(UserViewSet, self).create(request)
        subject = accounts_constants.SUBJECT
        message = accounts_constants.MESSAGE
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [response.data['email']]
        send_signup_mail.delay(subject, message, email_from, recipient_list)
        return response


class Login(CreateAPIView):
    '''
    View to send token to the user if successfully logggedin
    '''
    serializer_class = LoginSerializer


class LogoutView(DestroyAPIView):
    '''
    It deletes the token and logsout user
    '''
    authentication_classes = (TokenAuthentication, )
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request):
        Token.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
