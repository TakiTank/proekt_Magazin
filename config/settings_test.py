"""Test settings: sqlite for speed and zero external dependencies."""

from .settings import *  # noqa: F401,F403
from .settings import BASE_DIR

SECRET_KEY = "test-secret-key-with-enough-length-1234567890"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Fast password hashing in tests.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
