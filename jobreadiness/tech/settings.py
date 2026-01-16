from pathlib import Path
import os

import environ
import firebase_admin
from firebase_admin import credentials, firestore
from firebase_admin import credentials

# ==============================
# BASE DIR
# ==============================
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # adjust according to your project structure

# ==============================
# ENV CONFIG
# ==============================
env = environ.Env()
environ.Env.read_env(BASE_DIR / '.env') 

# ==============================
# FIREBASE CONFIG
# ==============================
if not firebase_admin._apps:
    cred = credentials.Certificate(env('FIREBASE_CREDENTIALS_FILE'))
    firebase_app = firebase_admin.initialize_app(cred, {
        'projectId': env('FIREBASE_PROJECT_ID'),
    })
FIRESTORE_CLIENT = firestore.client(app=firebase_app)
import os
from pathlib import Path
from firebase_admin import credentials, initialize_app

BASE_DIR = Path(__file__).resolve().parent.parent

cred_path = os.path.join(BASE_DIR, "serviceAccountKey.json")

if not firebase_admin._apps:
    initialize_app(credentials.Certificate(cred_path))


# ==============================
# DJANGO CONFIG
# ==============================
DEBUG = True  # Development mode
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]  # Local dev: allow all hosts
SECRET_KEY='django-insecure-3x!p7&y$k9w@q2r^v%t8z#b1n+f5j*m4h!c0l6u^d7e8g'



# ==============================
# INSTALLED APPS
# ==============================
INSTALLED_APPS = [
      
      'django_celery_beat',
  ]

DEFAULT_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
     'django_celery_beat',
]

THIRD_PARTY_APPS = [
]

LOCAL_APPS = [
    'users.apps.UsersConfig', 
    'skills',
    'core',
    'assessment',
]

INSTALLED_APPS = DEFAULT_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# Custom User model
AUTH_USER_MODEL = 'users.User'

# ==============================
# DJANGO MIDDLEWARE
# ==============================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',  # required
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',  # required
    'django.contrib.messages.middleware.MessageMiddleware',      # required
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ==============================
# DJANGO TEMPLATES
# ==============================
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

# ==============================
# URL CONFIG
# ==============================
ROOT_URLCONF = 'jobreadiness.tech.urls'

# ==============================
# WSGI / ASGI
# ==============================
WSGI_APPLICATION = 'jobreadiness.tech.wsgi.application'

# ==============================
# DATABASE (default SQLite)
# ==============================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ==============================
# PASSWORD VALIDATORS
# ==============================
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

# ==============================
# INTERNATIONALIZATION
# ==============================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# ==============================
# STATIC FILES
# ==============================
STATIC_URL = '/static/'

# ==============================
# DEFAULT PRIMARY KEY FIELD TYPE
# ==============================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==============================
# Celery Configuration
# ==============================
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

  # SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool('DEBUG', default=False)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])
  
  # CSRF
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG

