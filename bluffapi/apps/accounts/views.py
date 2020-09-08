from rest_framework import viewsets

from apps.accounts import (
    models as accounts_models, serializers as accounts_serializers,
)


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
