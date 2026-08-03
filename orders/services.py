"""Order creation: the core checkout business logic."""

from typing import Any

from django.db import transaction

from products.models import Product
from users.models import User

from .cart import Cart
from .models import Order, OrderItem


class InsufficientStock(Exception):
    """A cart line requests more units than are in stock."""

    def __init__(self, product: Product, available: int) -> None:
        self.product = product
        self.available = available
        super().__init__(f"{product.name}: only {available} available")


@transaction.atomic
def create_order(user: User, cart: Cart, **shipping: Any) -> Order:
    """Create an order from the cart, locking rows and decrementing stock.

    Payment is mocked: card/wallet orders are marked PAID immediately,
    cash-on-delivery stays PENDING. Raises InsufficientStock (and rolls
    back) if any line exceeds the available stock.
    """
    order = Order.objects.create(user=user, **shipping)
    total = order.total_price
    for item in cart:
        product = Product.objects.select_for_update().get(pk=item.product.pk)
        if item.quantity > product.stock:
            raise InsufficientStock(product, product.stock)
        product.stock -= item.quantity
        product.save(update_fields=["stock"])
        OrderItem.objects.create(
            order=order, product=product, quantity=item.quantity, price=product.price
        )
        total += product.price * item.quantity

    if order.payment_method != Order.PaymentMethod.COD:
        order.status = Order.Status.PAID  # mock payment succeeded

    order.total_price = total
    order.save(update_fields=["total_price", "status"])
    return order
