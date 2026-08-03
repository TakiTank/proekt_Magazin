"""Shared API helpers."""

from decimal import Decimal, InvalidOperation
from typing import Any, cast

from django.db.models import Avg, Count, QuerySet, Q, Sum
from django.db.models.functions import Coalesce

from orders.cart import Cart
from products.models import Product


def build_product_queryset() -> QuerySet[Product]:
    """Return the annotated product queryset used by the API."""
    return cast(
        Any,
        Product.objects.filter(is_active=True).select_related("category").annotate(
            avg_rating=Avg("reviews__rating"),
            review_count=Count("reviews", distinct=True),
            sold=Coalesce(Sum("order_items__quantity"), 0),
        ),
    )


def filter_products(queryset: QuerySet[Product], params: Any) -> QuerySet[Product]:
    """Apply search, category, price and ordering filters from query params."""
    queryset_any = cast(Any, queryset)
    q = params.get("q", "").strip()
    if q:
        queryset = queryset.filter(Q(name__icontains=q) | Q(description__icontains=q))

    categories = params.getlist("category")
    if categories:
        queryset = queryset.filter(category__slug__in=categories)

    for param, lookup in (("price_min", "price__gte"), ("price_max", "price__lte")):
        raw = params.get(param, "").strip()
        if not raw:
            continue
        try:
            queryset = queryset.filter(**{lookup: Decimal(raw)})
        except InvalidOperation:
            continue

    sort = params.get("sort", "new")
    if sort == "rating":
        return queryset_any.order_by("-avg_rating", "-created_at")
    if sort == "popular":
        return queryset_any.order_by("-sold", "-created_at")
    if sort == "price_asc":
        return queryset_any.order_by("price")
    if sort == "price_desc":
        return queryset_any.order_by("-price")
    return queryset.order_by("-created_at")


def cart_snapshot(cart: Cart) -> dict[str, Any]:
    """Serialize a session cart into a plain dictionary."""
    items = [
        {
            "product": item.product,
            "quantity": item.quantity,
            "total_price": item.total_price,
        }
        for item in cart
    ]
    return {"items": items, "total_quantity": len(cart), "total_price": cart.total_price}
