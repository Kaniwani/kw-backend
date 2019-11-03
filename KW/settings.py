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

import environ
import sentry_sdk
from celery.schedules import crontab
from django.utils.log import DEFAULT_LOGGING
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration

root = environ.Path(__file__) - 2
log_root = root.path("logs")

env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(root.path("KW").file(".env"))

LOGLEVEL = env("LOGLEVEL", default="INFO").upper()

# This allows the /docs/ endpoints to correctly build urls.
USE_X_FORWARDED_HOST = True
MY_TIME_ZONE = "America/New_York"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(name)s.%(funcName)s:%(lineno)s - %(message)s"
        }
    },
    "handlers": {
        "stdout": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": "kaniwani.log",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "KW": {"handlers": ["stdout", "file"], "level": LOGLEVEL},
        "kw_webapp": {"handlers": ["stdout", "file"], "level": LOGLEVEL},
        "api": {"handlers": ["stdout", "file"], "level": LOGLEVEL},
        "root": {"handlers": ["stdout", "file"], "level": LOGLEVEL},
        "django": {"handlers": ["stdout", "file"], "level": LOGLEVEL},
        "django.request": {"handlers": ["stdout", "file"], "level": LOGLEVEL},
        "django.db.backends": {
            "handlers": ["stdout", "file"],
            "level": "WARNING",
        },
        "django.security": {"handlers": ["stdout", "file"], "level": LOGLEVEL},
    },
}

REDIS_URL = env.cache_url("REDIS_URL", default="rediscache://localhost:6379/0")

CELERY_RESULT_BACKEND = REDIS_URL["LOCATION"]
CELERYD_HIJACK_ROOT_LOGGER = False
CELERY_BROKER_URL = REDIS_URL["LOCATION"]
CELERY_ACCEPT_CONTENT = ["application/json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULTS_SERIALIZER = "json"
CELERY_TIMEZONE = MY_TIME_ZONE
CELERY_BEAT_SCHEDULE = {
    "all_user_srs_every_hour": {
        "task": "kw_webapp.srs.all_srs",
        "schedule": crontab(minute="2"),
    },
    "update_users_unlocked_vocab": {
        "task": "kw_webapp.tasks.sync_all_users_to_wk",
        "schedule": timedelta(hours=12),
        "options": {"queue": "long_running_sync"},
    },
}

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "www.kaniwani.com",
    ".kaniwani.com",
    "0.0.0.0",
]

CORS_ORIGIN_WHITELIST = env.list("CORS_ORIGIN_WHITELIST")

CORS_ALLOW_CREDENTIALS = True

LOGIN_URL = "/api/v1/auth/login/"

INSTALLED_APPS = (
    "django.contrib.contenttypes",
    "kw_webapp.apps.KaniwaniConfig",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.humanize",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "debug_toolbar",
    "rest_framework.authtoken",
    "django_filters",
    "corsheaders",
    "djoser",
)

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.gzip.GZipMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "kw_webapp.middleware.SetLastVisitMiddleware",
]

if DEBUG:
    MIDDLEWARE += ["KW.LoggingMiddleware.ExceptionLoggingMiddleware"]

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly"
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_jwt.authentication.JSONWebTokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        # Simple overridden class which will dump empty JSON into the response if we find that the content is empty.
        "kw_webapp.renderers.FallbackJSONRenderer"
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 100,
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
    ),
}

CACHES = {"default": REDIS_URL}

ROOT_URLCONF = "KW.urls"

WSGI_APPLICATION = "KW.wsgi.application"

# EMAIL BACKEND SETTINGS
EMAIL_CONFIG = env.email_url("EMAIL_URL", default="dummymail://")
vars().update(EMAIL_CONFIG)

TIME_ZONE = MY_TIME_ZONE
SITE_ID = 1

DATABASES = {"default": env.db("DATABASE_URL", default="sqlite://db.sqlite3")}

DB_ENGINE = DATABASES["default"]["ENGINE"].split(".")[-1]

LANGUAGE_CODE = "en-us"
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = "/var/www/kaniwani.com/static"

# Security stuff
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = "DENY"
SESSION_COOKIE_SECURE = True


INTERNAL_IPS = ("127.0.0.1",)

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [root("templates"), root("kw_webapp/templates/kw_webapp")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.request",
                "django.contrib.messages.context_processors.messages",
            ],
            "debug": DEBUG,
        },
    }
]

MANAGERS = [
    ("Gary", "tadgh@cs.toronto.edu"),
    ("Duncan", "duncan.bay@gmail.com"),
]
DEFAULT_FROM_EMAIL = "gary@kaniwani.com"

JWT_AUTH = {"JWT_VERIFY_EXPIRATION": False}

AUTHENTICATION_BACKENDS = [
    "kw_webapp.backends.EmailOrUsernameAuthenticationBackend",
    "django.contrib.auth.backends.ModelBackend",
]


DJOSER = {
    "SERIALIZERS": {
        "user_create": "api.serializers.RegistrationSerializer",
        "current_user": "api.serializers.UserSerializer",
    },
    "PASSWORD_RESET_CONFIRM_URL": "password-reset/{uid}/{token}",
}

if not DEBUG:
    sentry_sdk.init(
        dsn=env("SENTRY_DSN"),
        integrations=[DjangoIntegration(), CeleryIntegration()],
    )
