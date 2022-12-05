"""
Django settings for integration_tiny project.

Generated by 'django-admin startproject' using Django 4.0.3.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.0/ref/settings/
"""

from pathlib import Path

import ldap
from celery.schedules import crontab
from decouple import config
# Build paths inside the project like this: BASE_DIR / 'subdir'.
from django_auth_ldap.config import LDAPSearch

BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-5w8)612gsdbwlz4$h2gw9x#h+f433%1lrdbd7pjk%sl)ki(yb8'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core'
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

ROOT_URLCONF = 'integration_tiny.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates']
        ,
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

WSGI_APPLICATION = 'integration_tiny.wsgi.application'

# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = 'pt-br'

TIME_ZONE = 'America/Sao_Paulo'

USE_I18N = True

USE_L10N = True

USE_TZ = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

BASE_URL_TINY = config('BASE_URL_TINY')
BASE_URL_INTEGRATOR = config('BASE_URL_INTEGRATOR')

CELERY_BROKER_URL = config('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = config('CELERY_BROKER_URL')
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

CELERY_BEAT_SCHEDULE = {
    'sync-orders': {
        'task': 'core.tasks.task_sync_orders',
        'schedule': crontab(minute='*/5'),
        'args': (-1,)
    },
    'sync-cancelled-orders': {
        'task': 'core.tasks.task_sync_cancelled_orders',
        'schedule': crontab(minute='*/5'),
        'args': (-1,)
    },
    'update-orders': {
        'task': 'core.tasks.task_update_orders',
        'schedule': crontab(minute='*/5'),
    },
    'search-expeditions': {
        'task': 'core.tasks.task_search_expeditions',
        'schedule': crontab(minute='*/5'),
    },
    'send-labels': {
        'task': 'core.tasks.task_send_labels',
        'schedule': crontab(minute='*/5'),
    }
}

AUTHENTICATION_BACKENDS = [
    'core.backend.MyLDAPBackend',
    'django.contrib.auth.backends.ModelBackend',
]

AUTH_LDAP_START_TLS = False
AUTH_LDAP_SERVER_URI = config('LDAP_HOST_URL')
AUTH_LDAP_BIND_DN = config('LDAP_USERNAME')
AUTH_LDAP_BIND_PASSWORD = config('LDAP_PASSWORD')
AUTH_LDAP_USER_SEARCH = LDAPSearch(
    "dc=netkeepers,dc=keepers,dc=com,dc=br",
    ldap.SCOPE_SUBTREE,
    "(sAMAccountName=%(user)s)"
)

AUTH_LDAP_CONNECTION_OPTIONS = {
    ldap.OPT_REFERRALS: 0,
}

AUTH_LDAP_USER_ATTR_MAP = {
    "username": "sAMAccountName",
    "first_name": "givenName",
    "last_name": "sn",
    "email": "mail",
}
