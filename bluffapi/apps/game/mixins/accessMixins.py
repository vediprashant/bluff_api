from rest_framework.permissions import IsAuthenticated

class LoggedInMixin():
    '''
    Returns 401 if request is not authenticated
    '''
    permission_classes = [IsAuthenticated]
    