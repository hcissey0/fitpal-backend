# rest/authentication.py
from rest_framework.authentication import TokenAuthentication


class CustomTokenAuthentication(TokenAuthentication):
    """
    Custom Token Authentication class that extends DRF's TokenAuthentication.
    This can be used to add custom behavior or logging if needed.
    """
    keyword = 'Bearer'  # Use 'Bearer' as the keyword for token authentication
