"""Reusable analytics helpers for Django admin pages."""

from __future__ import annotations

from decimal import Decimal

from django.db.models import Avg, Count, DecimalField, F, Sum, Value
from django.db.models.functions import Coalesce

from orders.models import Order
from products.models import Product, Review


def _money(value: Decimal | None) -> Decimal:
    return value if value is not None else Decimal("0")


def product_analytics(limit: int = 5) -> dict[str, object]:
    """Aggregate product catalog metrics and top-seller data."""
    total_stock = Product.objects.aggregate(total=Coalesce(Sum("stock"), Value(0)))["total"] or 0
    low_stock = Product.objects.filter(stock__lte=5).count()
    active_products = Product.objects.filter(is_active=True).count()
    total_reviews = Review.objects.count()
    avg_rating = Review.objects.aggregate(avg=Coalesce(Avg("rating"), Value(0.0)))["avg"] or 0.0
    top_products = list(
        Product.objects.annotate(
            sold_units=Coalesce(Sum("order_items__quantity"), Value(0)),
            orders_count=Coalesce(Count("order_items__order", distinct=True), Value(0)),
            revenue=Coalesce(
                Sum(
                    F("order_items__quantity") * F("order_items__price"),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                ),
                Value(Decimal("0"), output_field=DecimalField(max_digits=12, decimal_places=2)),
            ),
        )
        .order_by("-sold_units", "-revenue", "name")[:limit]
    )
    return {
        "analytics_title": "Catalog analytics",
        "analytics": [
            {"label": "Products", "value": Product.objects.count()},
            {"label": "Active products", "value": active_products},
            {"label": "Low stock products", "value": low_stock},
            {"label": "Total stock units", "value": total_stock},
            {"label": "Reviews", "value": total_reviews},
            {"label": "Average rating", "value": f"{avg_rating:.2f}"},
        ],
        "top_products_title": "Top products",
        "top_products": top_products,
    }


def order_analytics(limit: int = 5) -> dict[str, object]:
    """Aggregate order revenue and top-product metrics."""
    total_orders = Order.objects.count()
    paid_orders = Order.objects.filter(status__in=Order.PAID_STATUSES).count()
    revenue = Order.objects.filter(status__in=Order.PAID_STATUSES).aggregate(
        total=Coalesce(
            Sum("total_price"),
            Value(Decimal("0"), output_field=DecimalField(max_digits=12, decimal_places=2)),
        )
    )["total"]
    average_order = Order.objects.aggregate(
        avg=Coalesce(
            Avg("total_price"),
            Value(Decimal("0"), output_field=DecimalField(max_digits=12, decimal_places=2)),
        )
    )[
        "avg"
    ]
    top_products = list(
        Product.objects.annotate(
            sold_units=Coalesce(Sum("order_items__quantity"), Value(0)),
            orders_count=Coalesce(Count("order_items__order", distinct=True), Value(0)),
            revenue=Coalesce(
                Sum(
                    F("order_items__quantity") * F("order_items__price"),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                ),
                Value(Decimal("0"), output_field=DecimalField(max_digits=12, decimal_places=2)),
            ),
        )
        .filter(sold_units__gt=0)
        .order_by("-sold_units", "-revenue", "name")[:limit]
    )
    return {
        "analytics_title": "Order analytics",
        "analytics": [
            {"label": "Orders", "value": total_orders},
            {"label": "Paid orders", "value": paid_orders},
            {"label": "Revenue", "value": f"${_money(revenue):.2f}"},
            {"label": "Average order", "value": f"${_money(average_order):.2f}"},
        ],
        "top_products_title": "Top products by sales",
        "top_products": top_products,
    }
