from pathlib import Path
import os
import environ
import firebase_admin
from firebase_admin import credentials, firestore


# ==============================
# BASE DIR
# ==============================
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False)
)

environ.Env.read_env(BASE_DIR / '.env')

# ==============================
# FIREBASE CONFIG (INITIALIZE ONCE)
# ==============================
if not firebase_admin._apps:
    cred = credentials.Certificate(env('FIREBASE_CREDENTIALS_FILE'))
    firebase_app = firebase_admin.initialize_app(cred, {
        'projectId': env('FIREBASE_PROJECT_ID'),
    })

FIRESTORE_CLIENT = firestore.client()

# ==============================
# DJANGO CONFIG
# ==============================
DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
SECRET_KEY = 'django-insecure-CHANGE-ME-IN-PROD'

# ==============================
# INSTALLED APPS
# ==============================
DEFAULT_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_celery_beat',
]

# ==============================
# TEMPLATES (REQUIRED FOR ADMIN)
# ==============================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',  # REQUIRED
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


LOCAL_APPS = [
    'users',
    'skills',
    'core',
    'assessment',
    'learning',
    #'studyplan',     # <-- this is your real app name
    #'lesson',
]

INSTALLED_APPS = DEFAULT_APPS + LOCAL_APPS

AUTH_USER_MODEL = 'users.User'

# ==============================
# MIDDLEWARE
# ==============================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ==============================
# URLS / WSGI
# ==============================
ROOT_URLCONF = 'jobreadiness.urls'
WSGI_APPLICATION = 'jobreadiness.wsgi.application'

# ==============================
# DATABASE
# ==============================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ==============================
# I18N
# ==============================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ==============================
# STATIC FILES
# ==============================
STATIC_URL = '/static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==============================
# CELERY
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

GEMINI_API_KEY = "AIzaSyC8OLmeXXgM1sQlSIiP4buBw7AP9iwu8jQ"


GEMINI_MODEL_LITE = "models/gemini-pro"
GEMINI_MODEL_FLASH = "models/gemini-pro"
GEMINI_MODEL_PRO = "models/gemini-pro"



# =========================
# IRT Configuration
# =========================

IRT_CONVERGENCE_THRESHOLD = 0.3
IRT_MAX_QUESTIONS = 30

