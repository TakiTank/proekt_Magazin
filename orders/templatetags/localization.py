"""Localization helpers for order and payment labels."""

from django import template


register = template.Library()


STATUS_LABELS = {
    "uk": {
        "pending": "Очікує",
        "paid": "Оплачено",
        "shipped": "Відправлено",
        "delivered": "Доставлено",
        "cancelled": "Скасовано",
    },
    "en": {
        "pending": "Pending",
        "paid": "Paid",
        "shipped": "Shipped",
        "delivered": "Delivered",
        "cancelled": "Cancelled",
    },
}


PAYMENT_LABELS = {
    "uk": {
        "debit": "Банківська картка",
        "wallet": "Цифровий гаманець",
        "cod": "Оплата при отриманні",
    },
    "en": {
        "debit": "Debit card",
        "wallet": "Digital wallet",
        "cod": "Cash on delivery",
    },
}


@register.filter
def order_status_label(status: str, language: str = "uk") -> str:
    """Return a localized order status label."""
    return STATUS_LABELS.get(language, STATUS_LABELS["uk"]).get(status, status)


@register.filter
def payment_method_label(method: str, language: str = "uk") -> str:
    """Return a localized payment method label."""
    return PAYMENT_LABELS.get(language, PAYMENT_LABELS["uk"]).get(method, method)
