"""Catalog business rules."""

from django.contrib.auth.models import AbstractBaseUser, AnonymousUser

from orders.models import Order
from users.models import User

from .models import Product


def user_has_purchased(user: AbstractBaseUser | AnonymousUser, product: Product) -> bool:
    """True if the user has a non-cancelled order containing the product."""
    if not isinstance(user, User):
        return False
    return (
        Order.objects.filter(user=user, items__product=product)
        .exclude(status=Order.Status.CANCELLED)
        .exists()
    )
