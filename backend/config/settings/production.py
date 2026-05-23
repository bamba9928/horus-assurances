from django.core.exceptions import ImproperlyConfigured
from decouple import Csv, config

from .base import *  # noqa: F403

DEBUG = False

SECRET_KEY = config("DJANGO_SECRET_KEY", default="")
if not SECRET_KEY:
    raise ImproperlyConfigured("DJANGO_SECRET_KEY is required in production.")

ALLOWED_HOSTS = config("DJANGO_ALLOWED_HOSTS", default="", cast=Csv())
if not ALLOWED_HOSTS:
    raise ImproperlyConfigured("DJANGO_ALLOWED_HOSTS is required in production.")

SECURE_SSL_REDIRECT = config("DJANGO_SECURE_SSL_REDIRECT", default=True, cast=bool)
SECURE_HSTS_SECONDS = config("DJANGO_SECURE_HSTS_SECONDS", default=31536000, cast=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = config(
    "DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS",
    default=True,
    cast=bool,
)
SECURE_HSTS_PRELOAD = config("DJANGO_SECURE_HSTS_PRELOAD", default=True, cast=bool)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
