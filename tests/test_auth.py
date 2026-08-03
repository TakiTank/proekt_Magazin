import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


@pytest.mark.django_db
class TestAuth:
    def test_register_creates_user_and_logs_in(self, client) -> None:
        response = client.post(
            reverse("users:register"),
            {"email": "new@example.com", "password": "strong-pass-123", "remember_me": "on"},
        )
        assert response.status_code == 302
        assert User.objects.filter(email="new@example.com").exists()
        assert client.get(reverse("home")).context["user"].is_authenticated

    def test_register_rejects_weak_password(self, client) -> None:
        response = client.post(
            reverse("users:register"), {"email": "weak@example.com", "password": "123"}
        )
        assert response.status_code == 200
        assert not User.objects.filter(email="weak@example.com").exists()

    def test_login_with_email(self, client) -> None:
        User.objects.create_user(email="u@example.com", password="strong-pass-123")
        response = client.post(
            reverse("users:login"),
            {"username": "u@example.com", "password": "strong-pass-123"},
        )
        assert response.status_code == 302

    def test_logout(self, client) -> None:
        user = User.objects.create_user(email="u@example.com", password="x-pass-123456")
        client.force_login(user)
        client.post(reverse("users:logout"))
        assert not client.get(reverse("home")).context["user"].is_authenticated
