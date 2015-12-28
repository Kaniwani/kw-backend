"""
Django settings for KW project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
from collections import namedtuple
from datetime import timedelta
import os
from django.core.urlresolvers import reverse_lazy
import raven

try:
    import KW.secrets as secrets
except ImportError:
    print("Couldn't find a secrets file. Defaulting")
    secrets = namedtuple('secrets', ['DEPLOY', 'RAVEN_DSN', 'SECRET_KEY', 'DB_TYPE'])
    secrets.DB_TYPE = "sqlite"
    secrets.DEPLOY = False
    secrets.SECRET_KEY = "samplekey"
    secrets.RAVEN_DSN = "Whatever"

BASE_DIR = os.path.dirname(os.path.dirname(__file__))


sentry_class = 'raven.contrib.django.raven_compat.handlers.SentryHandler' if secrets.DEPLOY else 'logging.StreamHandler'
sentry_level = 'ERROR' if secrets.DEPLOY else 'DEBUG'

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
        'time_only': {
            'format': '%(asctime)s---%(message)s'
        }
    },
    'handlers': {
        'sentry': {
            'level': sentry_level,
            'class': sentry_class,
        },
        'views': {
            'level': 'DEBUG',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'when': 'midnight',
            'formatter': 'verbose',
            'filename': os.path.join(BASE_DIR, "logs", "views.log"),
        },
        'models': {
            'level': 'DEBUG',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'when': 'midnight',
            'formatter': 'verbose',
            'filename': os.path.join(BASE_DIR, "logs", "models.log"),
        },
        'errors': {
            'level': 'ERROR',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'when': 'midnight',
            'formatter': 'verbose',
            'filename': os.path.join(BASE_DIR, "logs", "errors.log"),
        },
        'tasks': {
            'level': 'INFO',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'when': 'midnight',
            'formatter': 'verbose',
            'filename': os.path.join(BASE_DIR, "logs", "tasks.log"),
        },
        'sporadic_tasks': {
            'level': 'INFO',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'when': 'midnight',
            'formatter': 'verbose',
            'filename': os.path.join(BASE_DIR, "logs", "sporadic_tasks.log"),
        },
        'review_data': {
            'level': 'INFO',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'when': 'midnight',
            'formatter': 'time_only',
            'filename': os.path.join(BASE_DIR, "logs", "review_data.log"),
        }
    },
    'loggers': {
        'kw.views': {
            'handlers': ['views', 'errors', 'sentry'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'kw.models': {
            'handlers': ['models', 'errors', 'sentry'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'kw.tasks': {
            'handlers': ['tasks', 'errors', 'sentry'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'kw.db_repopulator': {
            'handlers': ['sporadic_tasks', 'errors', 'sentry'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'kw.review_data': {
            'handlers':['review_data'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}


#CELERY SETTINGS
#CELERY_RESULT_BACKEND = 'amqp'
CELERY_RESULTS_BACKEND = 'redis://localhost:6379/0'
#BROKER_URL = broker = 'amqp://guest@localhost//'
BROKER_URL = 'redis://localhost:6379/0'
#CELERY_ACCEPT_CONTENT = ['json']
#CELERY_TASK_SERIALIZER = 'json'
#CELERY_RESULTS_SERIALIZER = 'json'
CELERY_TIMEZONE = 'America/New_York'
CELERYBEAT_SCHEDULE = {
    'all_user_srs_every_hour': {
        'task': 'kw_webapp.tasks.all_srs',
        'schedule': timedelta(minutes=15)
    },
    'update_users_unlocked_vocab': {
        'task': 'kw_webapp.tasks.sync_all_users_to_wk',
        'schedule': timedelta(hours=12)
    },
    'sync_vocab_db_with_wk': {
        'task': 'kw_webapp.tasks.repopulate',
        'schedule': timedelta(hours=3)

    }
}

#RAVEN DSN SETTINGS
RAVEN_CONFIG = {
    'dsn': secrets.RAVEN_DSN,
}


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = secrets.SECRET_KEY

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'www.kaniwani.com', '.kaniwani.com']

# Application definition


LOGIN_URL = reverse_lazy("kw:login")
LOGIN_REDIRECT_URL = reverse_lazy("kw:home")


CRISPY_TEMPLATE_PACK = 'bootstrap3'

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.humanize',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'kw_webapp',
    'crispy_forms',
    'raven.contrib.django.raven_compat',
    'rest_framework'
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = {
    'django.contrib.auth.context_processors.auth',
    "KW.preprocessors.review_count_preprocessor",
}

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated'
    ],
    'PAGE_SIZE': 10
}

ROOT_URLCONF = 'KW.urls'

WSGI_APPLICATION = 'KW.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

if secrets.DB_TYPE == "postgres":
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
elif secrets.DB_TYPE == "sqlite":
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
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
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "../_front-end/dist/assets"),
)
TEMPLATE_DIRS = (
    os.path.join(BASE_DIR,  'templates'),
    os.path.join(BASE_DIR,  'kw_webapp/templates/kw_webapp')
)
