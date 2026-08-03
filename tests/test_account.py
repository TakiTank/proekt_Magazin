import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from orders.models import Order, OrderItem
from products.models import Category, Product

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="me@example.com", password="pass-123456", first_name="Ivan"
    )


def _order(user, status: str) -> Order:
    return Order.objects.create(
        user=user, status=status, full_name="I", phone="1", city="K", address="a"
    )


@pytest.mark.django_db
class TestAccount:
    def test_requires_login(self, client) -> None:
        response = client.get(reverse("users:account"))
        assert response.status_code == 302 and "login" in response.url

    def test_prefills_profile_fields(self, client, user) -> None:
        user.phone = "+380501234567"
        user.city = "Lviv"
        user.address = "Rynok Square 1"
        user.save()
        client.force_login(user)
        html = client.get(reverse("users:account")).content.decode()
        assert "Кошик" in html
        assert 'value="Ivan"' in html
        assert 'value="me@example.com"' in html
        assert 'value="+380501234567"' in html
        assert 'value="Lviv"' in html
        assert "Rynok Square 1" in html

    def test_shows_own_orders_only(self, client, user) -> None:
        other = User.objects.create_user(email="other@example.com", password="x-123456")
        mine = _order(user, Order.Status.PENDING)
        theirs = _order(other, Order.Status.PENDING)
        client.force_login(user)
        html = client.get(reverse("users:account")).content.decode()
        assert f"#{mine.pk}" in html and f"#{theirs.pk}" not in html
        assert reverse("orders:detail", args=[mine.pk]) in html
        assert reverse("orders:reorder", args=[mine.pk]) in html
        assert "Замовити ще" in html

    def test_order_detail_requires_owner(self, client, user) -> None:
        category = Category.objects.create(name="Hops", slug="hops")
        product = Product.objects.create(
            name="Citra",
            slug="citra",
            description="d",
            price="5.99",
            category=category,
            stock=5,
        )
        mine = _order(user, Order.Status.PAID)
        OrderItem.objects.create(order=mine, product=product, quantity=2, price=product.price)
        other = User.objects.create_user(email="other@example.com", password="x-123456")
        theirs = _order(other, Order.Status.PAID)

        client.force_login(user)
        account_html = client.get(reverse("users:account")).content.decode()
        assert "Citra × 2" in account_html
        assert "Замовити ще" in account_html

        html = client.get(reverse("orders:detail", args=[mine.pk])).content.decode()
        assert "Citra" in html
        assert "Повернутися до замовлень" in html
        assert "Замовити ще" in html
        assert reverse("orders:reorder", args=[mine.pk]) in html
        assert client.get(reverse("orders:detail", args=[theirs.pk])).status_code == 404

        reorder = client.post(reverse("orders:reorder", args=[mine.pk]))
        assert reorder.status_code == 302
        assert reorder.url == reverse("orders:cart")
        assert client.session["cart"][str(product.pk)]["quantity"] == 2

    def test_filter_by_status(self, client, user) -> None:
        pending = _order(user, Order.Status.PENDING)
        delivered = _order(user, Order.Status.DELIVERED)
        client.force_login(user)
        html = client.get(reverse("users:account"), {"status": "delivered"}).content.decode()
        assert f"#{delivered.pk}" in html and f"#{pending.pk}" not in html

    def test_update_profile(self, client, user) -> None:
        client.force_login(user)
        response = client.post(
            reverse("users:account"),
            {"full_name": "Ivan Brewer", "email": "me@example.com",
             "phone": "+3805", "city": "Lviv", "address": "Rynok 1"},
        )
        assert response.status_code == 302
        assert response.url.endswith("?tab=account-info")
        user.refresh_from_db()
        assert user.last_name == "Brewer" and user.city == "Lviv"

    def test_invalid_profile_post_keeps_profile_tab_active(self, client, user) -> None:
        client.force_login(user)
        response = client.post(
            reverse("users:account"),
            {
                "full_name": "Ivan Brewer",
                "email": "",
                "phone": "+3805",
                "city": "Lviv",
                "address": "Rynok 1",
            },
        )
        assert response.status_code == 200
        html = response.content.decode()
        assert 'id="account-info" class="tab-pane active"' in html
        assert "errorlist" in html

    def test_change_password(self, client, user) -> None:
        client.force_login(user)
        response = client.post(
            reverse("users:password_change"),
            {"old_password": "pass-123456",
             "new_password1": "brand-new-pass-9", "new_password2": "brand-new-pass-9"},
        )
        assert response.status_code == 302
        user.refresh_from_db()
        assert user.check_password("brand-new-pass-9")
