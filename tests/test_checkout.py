from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.urls import reverse

from orders.models import Order
from products.models import Category, Product

User = get_user_model()

CHECKOUT_DATA = {
    "full_name": "Ivan Brewer", "phone": "+380501112233",
    "city": "Kyiv", "address": "Khreshchatyk 1", "payment_method": "debit",
}


@pytest.fixture
def product(db) -> Product:
    cat = Category.objects.create(name="Hops", slug="hops")
    return Product.objects.create(
        name="Citra", slug="citra", description="d",
        price=Decimal("5.99"), category=cat, stock=5,
    )


@pytest.fixture
def shopper(client, product: Product):
    user = User.objects.create_user(email="shopper@example.com", password="pass12345")
    client.force_login(user)
    client.post(reverse("orders:cart_add", args=[product.pk]), {"quantity": 2})
    return user


@pytest.mark.django_db
class TestCheckout:
    def test_requires_login(self, client, product: Product) -> None:
        response = client.get(reverse("orders:checkout"))
        assert response.status_code == 302 and "login" in response.url

    def test_creates_order_decrements_stock_sends_emails(
        self, client, shopper, product: Product
    ) -> None:
        response = client.post(reverse("orders:checkout"), CHECKOUT_DATA)
        order = Order.objects.get(user=shopper)
        assert response.status_code == 302
        assert order.total_price == Decimal("11.98")
        assert order.status == Order.Status.PAID  # debit → mock-paid
        assert order.items.get().price == Decimal("5.99")
        product.refresh_from_db()
        assert product.stock == 3
        assert client.session["cart"] == {}
        assert len(mail.outbox) == 2  # customer + admin notification

    def test_cod_stays_pending(self, client, shopper) -> None:
        client.post(reverse("orders:checkout"), {**CHECKOUT_DATA, "payment_method": "cod"})
        assert Order.objects.get().status == Order.Status.PENDING

    def test_insufficient_stock_rolls_back(self, client, shopper, product: Product) -> None:
        Product.objects.filter(pk=product.pk).update(stock=1)  # concurrent purchase
        response = client.post(reverse("orders:checkout"), CHECKOUT_DATA)
        assert Order.objects.count() == 0
        assert "Доступно лише" in response.content.decode()
        product.refresh_from_db()
        assert product.stock == 1

    def test_empty_cart_redirects(self, client) -> None:
        user = User.objects.create_user(email="empty@example.com", password="pass12345")
        client.force_login(user)
        response = client.get(reverse("orders:checkout"))
        assert response.status_code == 302
