"""Session-backed shopping cart.

Only quantities live in the session; prices are always read from the
database so the server stays the single source of truth.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterator

from django.conf import settings
from django.http import HttpRequest

from products.models import Product


class CartQuantityError(Exception):
    """Requested quantity exceeds the available stock."""

    def __init__(self, available: int) -> None:
        self.available = available
        super().__init__(f"Only {available} item(s) available")


@dataclass(frozen=True)
class CartItem:
    """A cart line joined with its live product."""

    product: Product
    quantity: int

    @property
    def total_price(self) -> Decimal:
        return self.product.price * self.quantity


class Cart:
    """Shopping cart stored in ``request.session``."""

    def __init__(self, request: HttpRequest) -> None:
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if cart is None:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self._items: dict[str, dict[str, int]] = cart

    def add(self, product: Product, quantity: int = 1, *, replace: bool = False) -> None:
        """Add ``quantity`` units (or set exactly, with ``replace=True``)."""
        current = 0 if replace else self._items.get(str(product.pk), {}).get("quantity", 0)
        self._set(product, current + quantity)

    def set_quantity(self, product: Product, quantity: int) -> None:
        """Set the line to an exact quantity; zero removes the line."""
        if quantity <= 0:
            self.remove(product)
            return
        self._set(product, quantity)

    def _set(self, product: Product, quantity: int) -> None:
        if quantity > product.stock:
            raise CartQuantityError(available=product.stock)
        self._items[str(product.pk)] = {"quantity": quantity}
        self._save()

    def remove(self, product: Product) -> None:
        """Drop the product line from the cart (no-op if absent)."""
        if self._items.pop(str(product.pk), None) is not None:
            self._save()

    def clear(self) -> None:
        """Empty the cart entirely."""
        self.session[settings.CART_SESSION_ID] = {}
        self._items = self.session[settings.CART_SESSION_ID]
        self._save()

    def quantity_of(self, product: Product) -> int:
        """Current quantity of the product in the cart (0 if absent)."""
        return self._items.get(str(product.pk), {}).get("quantity", 0)

    def __iter__(self) -> Iterator[CartItem]:
        products = Product.objects.filter(pk__in=self._items.keys())
        for product in products:
            yield CartItem(product=product, quantity=self._items[str(product.pk)]["quantity"])

    def __len__(self) -> int:
        return sum(line["quantity"] for line in self._items.values())

    @property
    def total_price(self) -> Decimal:
        """Sum of all line totals at current DB prices."""
        return sum((item.total_price for item in self), Decimal("0"))

    def _save(self) -> None:
        self.session.modified = True
