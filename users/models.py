"""Custom user model: email is the login identifier (the design has no username)."""

from typing import Any

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager["User"]):
    """Manager that creates users by email instead of username."""

    use_in_migrations = True

    def _create_user(self, email: str, password: str | None, **extra_fields: Any) -> "User":
        if not email:
            raise ValueError("The email address must be set")
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(
        self, email: str, password: str | None = None, **extra_fields: Any
    ) -> "User":
        """Create a regular (non-staff) user."""
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(
        self, email: str, password: str | None = None, **extra_fields: Any
    ) -> "User":
        """Create an admin user with full permissions."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Shop customer. Logs in with email; profile fields match the account page."""

    username = None  # type: ignore[assignment]
    email = models.EmailField("email address", unique=True)
    phone = models.CharField(max_length=32, blank=True)
    city = models.CharField(max_length=128, blank=True)
    address = models.TextField(blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []  # type: ignore[misc]

    objects = UserManager()  # type: ignore[assignment,misc]

    def __str__(self) -> str:
        return self.email

    @property
    def avatar_index(self) -> int:
        """Deterministic 1-10 index used to pick a review avatar SVG."""
        return (self.pk or 0) % 10 + 1
