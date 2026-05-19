import jwt
from datetime import datetime, timedelta
from django.conf import settings

def create_jwt_token(user_data):
    """Simple JWT token creation"""
    payload = {
       'user_id': str(user_data['id']),  # String, not int
        'username': user_data['username'],
        'is_admin': user_data.get('is_staff', False),
        'token_type': 'access',  # Required by SimpleJWT
        'exp': datetime.utcnow() + timedelta(hours=24),
        'iat': datetime.utcnow(),  # Required
        'jti': str(uuid.uuid4()),  # Required unique ID
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

def verify_jwt_token(token):
    """Simple JWT token verification"""
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
    except jwt.InvalidTokenError:
        return None
