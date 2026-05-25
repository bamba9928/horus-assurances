from datetime import timedelta
from pathlib import Path

from decouple import Csv, config

BASE_DIR = Path(__file__).resolve().parents[2]

SECRET_KEY = config("DJANGO_SECRET_KEY", default="unsafe-dev-key-change-me")
DEBUG = config("DJANGO_DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("DJANGO_ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=Csv())

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "drf_spectacular",
    "django_filters",
    "apps.groups",
    "apps.accounts",
    "apps.clients",
    "apps.vehicles",
    "apps.quotes",
    "apps.payments",
    "apps.contracts",
    "apps.ass_api",
    "apps.commissions",
    "apps.audit",
    "apps.notifications",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": config("DATABASE_ENGINE", default="django.db.backends.postgresql"),
        "NAME": config("DATABASE_NAME", default="horus_assurances"),
        "USER": config("DATABASE_USER", default="horus_user"),
        "PASSWORD": config("DATABASE_PASSWORD", default=""),
        "HOST": config("DATABASE_HOST", default="localhost"),
        "PORT": config("DATABASE_PORT", default="5432"),
    }
}

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Africa/Dakar"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_PAGINATION_CLASS": "apps.common.pagination.StandardResultsSetPagination",
    "PAGE_SIZE": config("API_PAGE_SIZE", default=20, cast=int),
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "anon": config("DRF_ANON_THROTTLE_RATE", default="100/hour"),
        "user": config("DRF_USER_THROTTLE_RATE", default="1000/hour"),
    },
}

CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:3000,http://127.0.0.1:3000",
    cast=Csv(),
)
CORS_ALLOW_CREDENTIALS = config("CORS_ALLOW_CREDENTIALS", default=True, cast=bool)

SPECTACULAR_SETTINGS = {
    "TITLE": "Horus Assurances API",
    "DESCRIPTION": "API backend Django pour Horus Assurances.",
    "VERSION": "0.12.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "ENUM_NAME_OVERRIDES": {
        "ContractStatusEnum": "apps.contracts.models.Contract.Status",
        "PaymentStatusEnum": "apps.payments.models.Payment.Status",
        "QuoteStatusEnum": "apps.quotes.models.Quote.Status",
        "PaymentWebhookEventStatusEnum": "apps.payments.models.PaymentWebhookEvent.Status",
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": False,
}

ASS_BASE_URL = config("ASS_BASE_URL", default="")
ASS_USERNAME = config("ASS_USERNAME", default="")
ASS_PASSWORD = config("ASS_PASSWORD", default="")
ASS_TIMEOUT_SECONDS = config("ASS_TIMEOUT_SECONDS", default=30, cast=int)

WAVE_WEBHOOK_SECRET = config("WAVE_WEBHOOK_SECRET", default="")
ORANGE_MONEY_WEBHOOK_SECRET = config("ORANGE_MONEY_WEBHOOK_SECRET", default="")
PAYMENT_WEBHOOK_TIMESTAMP_TOLERANCE_SECONDS = config(
    "PAYMENT_WEBHOOK_TIMESTAMP_TOLERANCE_SECONDS",
    default=300,
    cast=int,
)

CLIENT_ACCESS_TOKEN_TTL_DAYS = config(
    "CLIENT_ACCESS_TOKEN_TTL_DAYS",
    default=30,
    cast=int,
)
CLIENT_ACCESS_OTP_TTL_MINUTES = config(
    "CLIENT_ACCESS_OTP_TTL_MINUTES",
    default=10,
    cast=int,
)
CLIENT_ACCESS_OTP_LENGTH = config(
    "CLIENT_ACCESS_OTP_LENGTH",
    default=6,
    cast=int,
)
CLIENT_ACCESS_OTP_MAX_ATTEMPTS = config(
    "CLIENT_ACCESS_OTP_MAX_ATTEMPTS",
    default=5,
    cast=int,
)
CLIENT_PORTAL_BASE_URL = config(
    "CLIENT_PORTAL_BASE_URL",
    default="http://localhost:3000",
)
