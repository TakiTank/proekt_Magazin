import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    def test_create_user_with_email(self) -> None:
        user = User.objects.create_user(email="brewer@example.com", password="s3cret!pass")
        assert user.email == "brewer@example.com"
        assert user.check_password("s3cret!pass")
        assert not user.is_staff

    def test_create_superuser(self) -> None:
        admin = User.objects.create_superuser(email="admin@example.com", password="x")
        assert admin.is_staff and admin.is_superuser

    def test_email_is_required(self) -> None:
        with pytest.raises(ValueError):
            User.objects.create_user(email="", password="x")

    def test_email_unique(self) -> None:
        User.objects.create_user(email="a@a.com", password="x")
        with pytest.raises(Exception):
            User.objects.create_user(email="a@a.com", password="y")

    def test_avatar_index_in_range(self) -> None:
        user = User.objects.create_user(email="b@b.com", password="x")
        assert 1 <= user.avatar_index <= 10
