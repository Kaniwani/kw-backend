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
from collections import namedtuple
from django.core.urlresolvers import reverse_lazy

try:
    import KW.secrets as secrets
except ImportError:
    print("Couldn't find a secrets file. Defaulting")
    secrets = namedtuple('secrets', ['DEPLOY', 'SECRET_KEY', 'DB_TYPE'])
    secrets.DB_TYPE = "sqlite"
    secrets.DEPLOY = False
    secrets.SECRET_KEY = "samplekey"
    secrets.EMAIL_HOST_PASSWORD = "nope"
    secrets.EMAIL_HOST_USER = "dontmatter@whatever.com"

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
MY_TIME_ZONE = 'America/New_York'

logging_class = 'logging.StreamHandler'
logging_level = 'ERROR' if secrets.DEPLOY else 'DEBUG'


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
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
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
            'handlers': ['views', 'errors', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'kw.models': {
            'handlers': ['models', 'errors', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'kw.tasks': {
            'handlers': ['tasks', 'errors', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'kw.db_repopulator': {
            'handlers': ['sporadic_tasks', 'errors', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'kw.review_data': {
            'handlers':['review_data', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}


#CELERY SETTINGS
#CELERY_RESULT_BACKEND = 'amqp'
CELERY_RESULTS_BACKEND = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
#CELERY_BROKER_URL = broker = 'amqp://guest@localhost//'
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULTS_SERIALIZER = 'json'
CELERY_TIMEZONE = MY_TIME_ZONE
CELERY_BEAT_SCHEDULE = {
    'all_user_srs_every_hour': {
        'task': 'kw_webapp.tasks.all_srs',
        'schedule': timedelta(minutes=15)
    },
    'update_users_unlocked_vocab': {
        'task': 'kw_webapp.tasks.sync_all_users_to_wk',
        'schedule': timedelta(hours=12),
    },
    'sync_vocab_db_with_wk': {
        'task': 'kw_webapp.tasks.repopulate',
        'schedule': timedelta(hours=3)
    }
}


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = secrets.SECRET_KEY

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'www.kaniwani.com', '.kaniwani.com']

# Application definition

# CORS Settings
CORS_ORIGIN_WHITELIST = (
    'localhost:3000',
    'http://localhost:3000/',
    'http://127.0.0.1:3000',
    '127.0.0.1:3000'
)

CORS_ALLOW_CREDENTIALS = True

LOGIN_URL = reverse_lazy("login")
LOGIN_REDIRECT_URL = reverse_lazy("kw:home")


CRISPY_TEMPLATE_PACK = 'bootstrap3'

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.humanize',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_celery_beat',
    'crispy_forms',
    'rest_framework',
    'lineage',
    'kw_webapp.apps.KaniwaniConfig',
    'rest_framework_docs',
    'debug_toolbar',
    'rest_framework.authtoken',
    'corsheaders',
    'djoser'
)

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'kw_webapp.middleware.SetLastVisitMiddleware'
]

if DEBUG:
    MIDDLEWARE += [
        'KW.LoggingMiddleware.ExceptionLoggingMiddleware',
    ]

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated'
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_jwt.authentication.JSONWebTokenAuthentication',
        'rest_framework.authentication.SessionAuthentication'
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 100,
    'DEFAULT_FILTER_BACKENDS': ('django_filters.rest_framework.DjangoFilterBackend',)
}

REST_FRAMEWORK_DOCS = {
    'HIDE_DOCS': not DEBUG
}

CACHES = {
    'default': {
        'BACKEND': 'redis_cache.RedisCache',
        'LOCATION': 'localhost:6379'
    }
}

ROOT_URLCONF = 'KW.urls'

WSGI_APPLICATION = 'KW.wsgi.application'

#EMAIL BACKEND SETTINGS
MANAGERS = [("Gary", "tadgh@cs.toronto.edu",), ("Duncan", "duncan.bay@gmail.com")]
DEFAULT_FROM_EMAIL = "gary@kaniwani.com"
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = secrets.EMAIL_HOST_USER
EMAIL_HOST_PASSWORD = secrets.EMAIL_HOST_PASSWORD
EMAIL_PORT = 587
EMAIL_USE_TLS = True


TIME_ZONE = MY_TIME_ZONE
SITE_ID = 1

# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

if secrets.DB_TYPE == "postgres":
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
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

USE_I18N = True

USE_L10N = True

USE_TZ = True

LINEAGE_ANCESTOR_PHRASE = "-active"

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = "/var/www/kaniwani.com/static"
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "_front-end/dist/assets"),
)

INTERNAL_IPS = ('127.0.0.1',)

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            os.path.join(BASE_DIR,  'templates'),
            os.path.join(BASE_DIR,  'kw_webapp/templates/kw_webapp')
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                'django.contrib.auth.context_processors.auth',
                "KW.preprocessors.review_count_preprocessor",
                'django.template.context_processors.request',
                'django.contrib.messages.context_processors.messages',
            ],
            "debug": DEBUG
        }
    }
]

JWT_AUTH = {
        'JWT_VERIFY_EXPIRATION': False
}

AUTHENTICATION_BACKENDS = [
    'kw_webapp.backends.EmailOrUsernameAuthenticationBackend',
    'django.contrib.auth.backends.ModelBackend'
]

DJOSER = {
    'SERIALIZERS': {
        "user_registration": 'api.serializers.RegistrationSerializer'
    }
}
