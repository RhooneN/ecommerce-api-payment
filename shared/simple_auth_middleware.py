from django.http import JsonResponse
from .jwt_utils import verify_jwt_token

class SimpleAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Skip for non-API paths
        non_api_paths = ['/admin/', '/static/', '/auth/login/', '/auth/register/']
        if any(request.path.startswith(path) for path in non_api_paths):
            return self.get_response(request)
        
        # Skip for OPTIONS requests (CORS preflight)
        if request.method == 'OPTIONS':
            return self.get_response(request)
        
        # Only apply to API routes
        if request.path.startswith('/api/'):
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            if not auth_header.startswith('Bearer '):
                return JsonResponse({'error': 'Authentication required'}, status=401)
            
            token = auth_header.split(' ')[1]
            payload = verify_jwt_token(token)
            
            if not payload:
                return JsonResponse({'error': 'Invalid token'}, status=401)
            
            request.user_id = payload['user_id']
            request.is_admin = payload.get('is_admin', False)
        
        return self.get_response(request)
