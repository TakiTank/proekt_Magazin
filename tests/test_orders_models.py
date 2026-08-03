from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from orders.models import Order, OrderItem
from products.models import Category, Product

User = get_user_model()


@pytest.mark.django_db
def test_order_item_keeps_price_snapshot() -> None:
    user = User.objects.create_user(email="buyer@example.com", password="x")
    cat = Category.objects.create(name="Hops", slug="hops")
    product = Product.objects.create(
        name="Citra", slug="citra", description="d", price=Decimal("5.99"),
        category=cat, stock=5,
    )
    order = Order.objects.create(
        user=user, full_name="Ivan Brewer", phone="+380501112233",
        city="Kyiv", address="Khreshchatyk 1",
    )
    item = OrderItem.objects.create(order=order, product=product, quantity=3, price=product.price)

    product.price = Decimal("9.99")
    product.save()

    item.refresh_from_db()
    assert item.price == Decimal("5.99")
    assert item.total_price == Decimal("17.97")
    assert order.status == Order.Status.PENDING
