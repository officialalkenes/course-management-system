import os
from urllib.parse import urlparse
from .base import *  # noqa
from dotenv import load_dotenv

load_dotenv()


tmpPostgres = urlparse(os.getenv("DATABASE_URL"))  # noqa

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": tmpPostgres.path.replace(b"/", b"")
        if isinstance(tmpPostgres.path, bytes)
        else tmpPostgres.path.replace("/", ""),
        "USER": tmpPostgres.username,
        "PASSWORD": tmpPostgres.password,
        "HOST": tmpPostgres.hostname,
        "PORT": 5432,
    }
}

STATIC_URL = "/static/"
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]  # noqa
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")  # noqa


MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")  # noqa


# Dev-only apps/middleware
INSTALLED_APPS += [  # noqa
    "django_extensions",
    "debug_toolbar",
    # "django_debug_toolbar",
]

# MIDDLEWARE += [
#     "debug_toolbar.middleware.DebugToolbarMiddleware",
# ]


EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")  # noqa
EMAIL_PORT = os.getenv("EMAIL_PORT", default=587)  # noqa
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", default=True)  # Cast to boolean #noqa
EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL", default=False)  # noqa
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "belloabdulhakeemolamide@gmail.com")  # noqa
EMAIL_HOST_PASSWORD = os.getenv(  # noqa
    "EMAIL_HOST_PASSWORD", ""
)

DEFAULT_FROM_EMAIL = os.getenv(
    "DEFAULT_FROM_EMAIL", "belloabdulhakeemolamide@gmail.com"
)  # noqa
