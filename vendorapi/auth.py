from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from vendorapi.models import VendorApiKey


class APIKeyAuth(BaseAuthentication):
    def authenticate(self, request):
        api_key = request.headers.get("x-api-key")

        if not api_key:
            raise AuthenticationFailed("Missing API key")

        try:
            api_key_obj = VendorApiKey.objects.get(key=api_key)
        except VendorApiKey.DoesNotExist:
            raise AuthenticationFailed("Invalid API key")

        vendor = api_key_obj.vendor
        return (vendor.created_by, vendor)  # user, vendor
