"""
Django settings for payments service project (localhost:8005)
"""

from pathlib import Path
from dotenv import load_dotenv
load_dotenv()  # 👈 Loads from payment-service/.env
from decouple import config
import os

load_dotenv()
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'django-insecure-36s$aukd6*njaanwj65v4ed1nil=0yg6ju2c@p0f0bq#b^@15%')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['payment', "orders", "notif", '127.0.0.1' ,
    "authentic",
    "shopping_cart",
    "catalog",
    "localhost",
    'auth-service',  # For Docker compatibility
    'app']
    
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8000",  # Auth service
    "http://127.0.0.1:8000",  # Auth service
    "http://localhost:8001",  # Product service
    "http://127.0.0.1:8001",  # Product service
    "http://localhost:8002",  # cart service
    "http://127.0.0.1:8002",  # cart service
    "http://localhost:8003",  # This cart service
    "http://127.0.0.1:8003",  # This cart service
]


ORDER_SERVICE_URL = os.environ.get('ORDER_SERVICE_URL', 'http://localhost:8003/')  
ORDER_SERVICE_TOKEN = os.environ.get('ORDER_SERVICE_TOKEN', '')  # Optional auth token



BASE_URL = 'http://localhost:8005'  # payment service URL

# Application definition
INSTALLED_APPS = [
    'app',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'paypal.standard.ipn',
    'paypalrestsdk',
    "django_prometheus",
     'drf_spectacular',
    'drf_spectacular_sidecar',  # required for Django collectstatic discovery
    ]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',  
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'shared.simple_auth_middleware.SimpleAuthMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    "django_prometheus.middleware.PrometheusAfterMiddleware",
]

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated'
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'user': '100/day',
        'anon': '10/hour',
    },
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'payment.auth.JWTAuth',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Your Project API',
    'DESCRIPTION': 'Your project description',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
     'SWAGGER_UI_DIST': 'SIDECAR',  # shorthand to use the sidecar instead
    'SWAGGER_UI_FAVICON_HREF': 'SIDECAR',
    'REDOC_DIST': 'SIDECAR',
    # OTHER SETTINGS
}

# Cache configuration for Django cache framework
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'cart-service-cache',
        'TIMEOUT': 300,  # 5 minutes default
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
        }
    }
}

# Session configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_SAVE_EVERY_REQUEST = True

CSRF_COOKIE_SECURE = False
CSRF_COOKIE_HTTPONLY = False
LOGIN_URL = "http://127.0.0.1:8000/auth/login/"

ROOT_URLCONF = 'payment.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'payment.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

STATICFILES_DIRS = (os.path.join(BASE_DIR, 'static/'),)
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============================================
# LOGGING CONFIGURATION FOR DEBUGGING
# ============================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'cart_service.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'app.serializers': {  
            'handlers': ['file', 'console'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': True,
        },
        'requests': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'WARNING',
            'propagate': True,
        },
    },
}

# PayPal Configuration
import paypalrestsdk
paypalrestsdk.configure({
    "mode": "sandbox",  
    "client_id": config("client_id"),#"ASKLfmKE3cJwkZLhdzE0bpmSWDwyGWDIKGrkC40M5mI4pUONU1UFCLm2PI_ksNg5FPUGqJWPTbrdvlNA",
    "client_secret": config("client_secret")# "EN1pwXWVvms_TV_4lnHFobaJ3nokktMZNqrx0JZ7NWxSpVq1WZDtSnirZk7ocVbsOEWEB7Q5nUt9tmYh"
})
