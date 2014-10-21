"""
Django settings for KW project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
from datetime import timedelta
import os
from django.core.urlresolvers import reverse_lazy
import KW.secrets as secrets

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
    'verbose': {
        'format': '%(levelname)s---%(asctime)s---%(module)s : %(message)s',
      },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'views': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'formatter': 'verbose',
            'filename': os.path.join(BASE_DIR, "logs", "views.log"),
        },
        'models': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'formatter': 'verbose',
            'filename': os.path.join(BASE_DIR, "logs", "models.log"),
        },
        'errors': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'formatter': 'verbose',
            'filename': os.path.join(BASE_DIR, "logs", "errors.log"),
        },
        'tasks': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'formatter': 'verbose',
            'filename': os.path.join(BASE_DIR, "logs", "tasks.log"),
        },
	'sporadic_tasks': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'formatter': 'verbose',
            'filename': os.path.join(BASE_DIR, "logs", "sporadic_tasks.log"),
	}
    },
    'loggers': {
        'kw.views': {
            'handlers': ['views', 'errors'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'kw.models': {
            'handlers': ['models', 'errors'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'kw.tasks': {
            'handlers': ['tasks', 'errors'],
            'level': 'DEBUG',
            'propagate': True,
        },
	'kw.db_repopulator': {
            'handlers': ['sporadic_tasks', 'errors'],
            'level': 'DEBUG',
            'propagate': True,
	},
    },
}


#CELERY SETTINGS
CELERY_RESULT_BACKEND = 'amqp'
BROKER_URL = broker = 'amqp://guest@localhost//'
CELERY_TIMEZONE = 'America/New_York'
CELERYBEAT_SCHEDULE = {
    'all_user_srs_every_hour': {
        'task': 'kw_webapp.tasks.all_srs',
        'schedule': timedelta(minutes=15)
    },
}


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = secrets.SECRET_KEY

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []

# Application definition


LOGIN_URL = reverse_lazy("kw:login")
LOGIN_REDIRECT_URL = reverse_lazy("kw:home")


CRISPY_TEMPLATE_PACK = 'bootstrap3'
SOUTH_TESTS_MIGRATE = False

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'kw_webapp',
    'south',
    'crispy_forms',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'KW.urls'

WSGI_APPLICATION = 'KW.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': secrets.DB_NAME,
        'USER': secrets.DB_USER,
        'PASSWORD': secrets.DB_PASSWORD,
        'HOST': 'localhost',
        'PORT': '',
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/New_York'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = "/opt/venvs/KaniWaniEnv/KW/kw_webapp/static"
TEMPLATE_DIRS = (
    os.path.join(BASE_DIR,  'templates'),
)
