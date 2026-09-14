"""
Django settings for root project.

Maxfiy qiymatlar `.env` faylidan o'qiladi (django-environ).
Namuna: `.env.example`
"""

from datetime import timedelta
from pathlib import Path

import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("DJANGO_SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool("DJANGO_DEBUG", default=False)

ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'drf_spectacular',
    'django_filters',

    # Local apps
    'users.apps.UsersConfig',
    'product',
    'order',
    'analytics',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'root.urls'

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

WSGI_APPLICATION = 'root.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom user model — login phone_number orqali (TZ 3.2)
AUTH_USER_MODEL = 'users.User'


# Tasdiqlash kodi (TZ 3.3 / 4-bo'lim)
VERIFICATION_CODE_LENGTH = env.int('VERIFICATION_CODE_LENGTH', default=6)
VERIFICATION_CODE_TTL_MINUTES = env.int('VERIFICATION_CODE_TTL_MINUTES', default=5)
VERIFICATION_CODE_MAX_ATTEMPTS = env.int('VERIFICATION_CODE_MAX_ATTEMPTS', default=5)
VERIFICATION_CODE_RESEND_SECONDS = env.int('VERIFICATION_CODE_RESEND_SECONDS', default=60)


# Media (avatar yuklash uchun)
MEDIA_URL = env('MEDIA_URL', default='/media/')
MEDIA_ROOT = BASE_DIR / 'media'


# Django REST Framework (TZ 6-bo'lim)
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    # Default — yopiq. Ochiq endpointda view'ning o'zida AllowAny yoziladi.
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_THROTTLE_RATES': {
        'anon': env('THROTTLE_ANON', default='100/hour'),
        'user': env('THROTTLE_USER', default='1000/hour'),
        'auth': env('THROTTLE_AUTH', default='10/hour'),
    },
}


# JWT — access 30 daqiqa, refresh 7 kun (TZ 1-bo'lim)
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(
        minutes=env.int('ACCESS_TOKEN_LIFETIME_MINUTES', default=30)
    ),
    'REFRESH_TOKEN_LIFETIME': timedelta(
        days=env.int('REFRESH_TOKEN_LIFETIME_DAYS', default=7)
    ),
    'ROTATE_REFRESH_TOKENS': env.bool('ROTATE_REFRESH_TOKENS', default=True),
    'BLACKLIST_AFTER_ROTATION': env.bool('BLACKLIST_AFTER_ROTATION', default=True),
    'SIGNING_KEY': env('JWT_SIGNING_KEY', default='') or SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}


# drf-spectacular — Swagger / Redoc (TZ S0-06)
SPECTACULAR_SETTINGS = {
    'TITLE': 'CRM + Savdo tizimi API',
    'DESCRIPTION': (
        "Kichik CRM va onlayn savdo tizimi API hujjati.\n\n"
        "**Autentifikatsiya:** `POST /api/v1/auth/token/` orqali `access` token oling, "
        "so'ng o'ng yuqoridagi **Authorize** tugmasini bosib `Bearer <access>` ni kiriting.\n\n"
        "Eslatma: user ro'yxatdan o'tganda `is_active=False` bo'ladi — token olish uchun "
        "avval akkaunt tasdiqlanishi kerak."
    ),
    'VERSION': '1.0.0',
    # Schema'ning o'zi endpointlar ro'yxatida ko'rinmasin
    'SERVE_INCLUDE_SCHEMA': False,
    # /api/v1/ prefiksi operation nomlaridan olib tashlanadi
    'SCHEMA_PATH_PREFIX': '/api/v1',
    # multipart (avatar) va json body'ni alohida ko'rsatadi
    'COMPONENT_SPLIT_REQUEST': True,
    'SORT_OPERATIONS': False,
    'SWAGGER_UI_SETTINGS': {
        'persistAuthorization': True,
        'displayRequestDuration': True,
        'filter': True,
    },
    'TAGS': [
        {'name': 'auth', 'description': "Ro'yxatdan o'tish, token va profil"},
        {'name': 'catalog', 'description': "Kategoriyalar va mahsulotlar"},
    ],
}
