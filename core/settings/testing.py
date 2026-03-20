"""
Django testing settings.
Uses SQLite for faster tests.
"""
from .base import *

DEBUG = False

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "test_db.sqlite3",
    }
}

CORS_ALLOW_ALL_ORIGINS = True

STATIC_URL = "/static/"
MEDIA_URL = "/media/"

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
