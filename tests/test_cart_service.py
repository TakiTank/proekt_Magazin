from decimal import Decimal

import pytest
from django.test import RequestFactory

from orders.cart import Cart, CartQuantityError
from products.models import Category, Product


@pytest.fixture
def product(db) -> Product:
    cat = Category.objects.create(name="Hops", slug="hops")
    return Product.objects.create(
        name="Citra", slug="citra", description="d",
        price=Decimal("5.99"), category=cat, stock=5,
    )


@pytest.fixture
def cart(client) -> Cart:
    """Cart bound to a real session from the test client."""
    request = RequestFactory().get("/")
    request.session = client.session
    return Cart(request)


@pytest.mark.django_db
class TestCart:
    def test_add_and_totals(self, cart: Cart, product: Product) -> None:
        cart.add(product, 2)
        assert len(cart) == 2
        assert cart.total_price == Decimal("11.98")
        items = list(cart)
        assert items[0].product == product
        assert items[0].total_price == Decimal("11.98")

    def test_add_accumulates_and_replace(self, cart: Cart, product: Product) -> None:
        cart.add(product, 2)
        cart.add(product, 1)
        assert len(cart) == 3
        cart.add(product, 1, replace=True)
        assert len(cart) == 1

    def test_stock_limit(self, cart: Cart, product: Product) -> None:
        with pytest.raises(CartQuantityError) as exc:
            cart.add(product, 6)
        assert exc.value.available == 5
        assert len(cart) == 0

    def test_set_quantity_zero_removes(self, cart: Cart, product: Product) -> None:
        cart.add(product, 2)
        cart.set_quantity(product, 0)
        assert len(cart) == 0

    def test_clear(self, cart: Cart, product: Product) -> None:
        cart.add(product)
        cart.clear()
        assert len(cart) == 0

    def test_price_always_fresh_from_db(self, cart: Cart, product: Product) -> None:
        cart.add(product, 1)
        Product.objects.filter(pk=product.pk).update(price=Decimal("7.00"))
        assert cart.total_price == Decimal("7.00")
