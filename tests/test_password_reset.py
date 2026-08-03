import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.urls import reverse


@pytest.mark.django_db
def test_password_reset_sends_email(client) -> None:
    get_user_model().objects.create_user(email="lost@example.com", password="old-pass-123")
    response = client.post(reverse("users:password_reset"), {"email": "lost@example.com"})
    assert response.status_code == 302
    assert len(mail.outbox) == 1
    assert "lost@example.com" in mail.outbox[0].to
