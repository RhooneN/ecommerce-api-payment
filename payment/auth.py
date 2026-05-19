# products/authentication.py
from rest_framework_simplejwt.authentication import JWTAuthentication

#this first clas obj would require the service to have the user and will sync with user-service what i dont want,

class CustomJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        """
        Override the default method to also pull custom claims (is_admin).
        """
        user = super().get_user(validated_token)

        # Inject custom claims from the token into the user object (not persisted in DB)
        is_admin = validated_token.get("is_admin", False)
        setattr(user, "is_admin", is_admin)

        return user
#this will use the token to create a fake user for the product, what i really want
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
import jwt
from django.conf import settings

class JWTAuth(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed("Token expired")
        except jwt.InvalidTokenError:
            raise AuthenticationFailed("Invalid token")

        # 👇 Instead of User, just return a "proxy user"
        user = type("User", (), payload)
        return (user, None)
