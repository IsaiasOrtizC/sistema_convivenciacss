"""
Django settings for config project.
"""

import os
import sys
from datetime import timedelta
from pathlib import Path

import cloudinary
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

# Correo (Resend)
RESEND_API_KEY = os.getenv('RESEND_API_KEY')
RESEND_FROM_EMAIL = os.getenv(
    'RESEND_FROM_EMAIL',
    'ConviData <onboarding@resend.dev>',
)

# Seguridad y entorno
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY and not DEBUG:
    raise RuntimeError('La variable de entorno SECRET_KEY es obligatoria cuando DEBUG=False.')

TRAZA_NIVEL = int(os.getenv('TRAZA_NIVEL', '1' if DEBUG or 'runserver' in sys.argv else '0'))

_raw_hosts = os.getenv('ALLOWED_HOSTS', '').strip()
if _raw_hosts:
    ALLOWED_HOSTS = [h.strip() for h in _raw_hosts.split(',') if h.strip()]
elif DEBUG:
    ALLOWED_HOSTS = ['*']
else:
    ALLOWED_HOSTS = ['.onrender.com', '.trycloudflare.com', 'localhost', '127.0.0.1']


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.postgres',
    'cloudinary_storage',
    'django.contrib.staticfiles',
    'cloudinary',
    'rest_framework',
    'gestion_casos',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'gestion_casos.trazabilidad.TrazabilidadMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'gestion_casos.middleware.ForzarSesionUnicaMiddleware',
    'gestion_casos.middleware.ExigirCambioContrasenaMiddleware',
    'gestion_casos.trazabilidad.TrazabilidadControladorMiddleware',
]

ROOT_URLCONF = 'config.urls'

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

WSGI_APPLICATION = 'config.wsgi.application'


# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'postgres'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'CONN_MAX_AGE': int(os.getenv('DB_CONN_MAX_AGE', '60')),
    }
}


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Internationalization
LANGUAGE_CODE = 'es-cl'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True


# Static & Media files
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.getenv('CLOUDINARY_CLOUD_NAME', ''),
    'API_KEY': os.getenv('CLOUDINARY_API_KEY', ''),
    'API_SECRET': os.getenv('CLOUDINARY_API_SECRET', ''),
}

cloudinary.config(
    cloud_name=CLOUDINARY_STORAGE['CLOUD_NAME'],
    api_key=CLOUDINARY_STORAGE['API_KEY'],
    api_secret=CLOUDINARY_STORAGE['API_SECRET'],
    secure=True,
)

STORAGES = {
    'default': {
        'BACKEND': 'cloudinary_storage.storage.MediaCloudinaryStorage',
    },
    'staticfiles': {
        'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
    },
}

MEDIA_URL = '/media/'


# Límites para extracción y OCR de reglamentos y protocolos
REGLAMENTO_PDF_MAX_BYTES = int(
    os.getenv('REGLAMENTO_PDF_MAX_BYTES', str(20 * 1024 * 1024))
)
REGLAMENTO_PDF_MAX_PAGES = int(os.getenv('REGLAMENTO_PDF_MAX_PAGES', '500'))
REGLAMENTO_PDF_MIN_TEXT_CHARS = int(
    os.getenv('REGLAMENTO_PDF_MIN_TEXT_CHARS', '30')
)
REGLAMENTO_PDF_MIN_USEFUL_CHARS = int(
    os.getenv('REGLAMENTO_PDF_MIN_USEFUL_CHARS', '30')
)
REGLAMENTO_OCR_MAX_PAGES = int(os.getenv('REGLAMENTO_OCR_MAX_PAGES', '50'))
REGLAMENTO_OCR_DPI = int(os.getenv('REGLAMENTO_OCR_DPI', '200'))
REGLAMENTO_OCR_TIMEOUT_SECONDS = int(
    os.getenv('REGLAMENTO_OCR_TIMEOUT_SECONDS', '30')
)
TESSERACT_CMD = os.getenv('TESSERACT_CMD', '')
TESSDATA_PREFIX = os.getenv('TESSDATA_PREFIX', '')
DATA_UPLOAD_MAX_MEMORY_SIZE = REGLAMENTO_PDF_MAX_BYTES
FILE_UPLOAD_MAX_MEMORY_SIZE = REGLAMENTO_PDF_MAX_BYTES

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Django REST Framework & JWT
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'gestion_casos.authentication.UsuarioJWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'AUTH_HEADER_TYPES': ('Bearer',),
}


# Proxy, iframe y seguridad HTTPS
X_FRAME_OPTIONS = 'SAMEORIGIN'
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_CONTENT_TYPE_NOSNIFF = True

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'

_extra_csrf = [
    origin.strip()
    for origin in os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',')
    if origin.strip()
]
CSRF_TRUSTED_ORIGINS = [
    'https://*.trycloudflare.com',
    'http://*.trycloudflare.com',
    'https://his-champagne-taste-comparable.trycloudflare.com',
    *_extra_csrf,
]


# Celery
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://127.0.0.1:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://127.0.0.1:6379/0')
CELERY_TASK_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'America/Santiago'
CELERY_ENABLE_UTC = True