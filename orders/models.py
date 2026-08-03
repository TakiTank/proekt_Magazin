"""Order models: an order with line items snapshotting the purchase price."""

from decimal import Decimal

from django.conf import settings
from django.db import models


class Order(models.Model):
    """A customer order created from the cart at checkout."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        SHIPPED = "shipped", "Shipped"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"

    class PaymentMethod(models.TextChoices):
        DEBIT = "debit", "Debit Card"
        WALLET = "wallet", "Digital Wallet"
        COD = "cod", "Cash On Delivery"

    #: Statuses that count as revenue in admin analytics.
    PAID_STATUSES = (Status.PAID, Status.SHIPPED, Status.DELIVERED)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="orders"
    )
    status = models.CharField(max_length=16, choices=Status, default=Status.PENDING)
    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=32)
    city = models.CharField(max_length=128)
    address = models.TextField()
    payment_method = models.CharField(
        max_length=16, choices=PaymentMethod, default=PaymentMethod.DEBIT
    )
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Order #{self.pk}"


class OrderItem(models.Model):
    """A single product line inside an order; `price` is frozen at purchase time."""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        "products.Product", on_delete=models.PROTECT, related_name="order_items"
    )
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self) -> str:
        return f"{self.product} x{self.quantity}"

    @property
    def total_price(self) -> Decimal:
        """Line total: unit price snapshot times quantity."""
        return self.price * self.quantity
