"""Order notification emails (console backend in development)."""

from django.conf import settings
from django.core.mail import send_mail

from .models import Order


def send_order_emails(order: Order) -> None:
    """Email the customer a confirmation and notify the shop admin."""
    lines = "\n".join(
        f"  {item.product.name} x{item.quantity} - ${item.total_price}"
        for item in order.items.select_related("product")
    )
    body = (
        f"Hi {order.full_name},\n\n"
        f"Thanks for your order #{order.pk}!\n\n{lines}\n\n"
        f"Total: ${order.total_price}\n"
        f"Shipping to: {order.city}, {order.address}\n"
    )
    send_mail(
        subject=f"Hop & Barley - order #{order.pk} confirmed",
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[order.user.email],
    )
    send_mail(
        subject=f"New order #{order.pk} - ${order.total_price}",
        message=f"Order #{order.pk} by {order.user.email}.\n\n{lines}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[settings.ORDER_NOTIFICATION_EMAIL],
    )
