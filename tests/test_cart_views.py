from decimal import Decimal

import pytest
from django.urls import reverse

from products.models import Category, Product


@pytest.fixture
def product(db) -> Product:
    cat = Category.objects.create(name="Hops", slug="hops")
    return Product.objects.create(
        name="Citra", slug="citra", description="d",
        price=Decimal("5.99"), category=cat, stock=5,
    )


@pytest.mark.django_db
class TestCartViews:
    def test_add_and_view(self, client, product: Product) -> None:
        client.post(reverse("orders:cart_add", args=[product.pk]), {"quantity": 2})
        assert client.session["cart"][str(product.pk)]["quantity"] == 2
        html = client.get(reverse("orders:cart")).content.decode()
        assert "cart-total-price" in html
        assert "Замовити ще" in html
        assert reverse("home") in html

    def test_add_over_stock_shows_error(self, client, product: Product) -> None:
        response = client.post(
            reverse("orders:cart_add", args=[product.pk]), {"quantity": 99}, follow=True
        )
        assert "Доступно лише" in response.content.decode()
        assert client.session.get("cart") in (None, {})

    def test_update_quantity(self, client, product: Product) -> None:
        client.post(reverse("orders:cart_add", args=[product.pk]), {"quantity": 2})
        client.post(reverse("orders:cart_update", args=[product.pk]), {"quantity": 1})
        assert client.session["cart"][str(product.pk)]["quantity"] == 1

    def test_remove(self, client, product: Product) -> None:
        client.post(reverse("orders:cart_add", args=[product.pk]), {"quantity": 1})
        client.post(reverse("orders:cart_remove", args=[product.pk]))
        assert client.session["cart"] == {}

    def test_get_not_allowed_for_mutations(self, client, product: Product) -> None:
        response = client.get(reverse("orders:cart_add", args=[product.pk]))
        assert response.status_code == 405

    def test_empty_cart_page(self, client) -> None:
        html = client.get(reverse("orders:cart")).content.decode()
        assert "Кошик порожній" in html
