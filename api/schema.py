"""GraphQL schema: catalog queries and shop analytics."""

from __future__ import annotations

from decimal import Decimal

import graphene
from django.db.models import Avg, Count, DecimalField, Q, Sum, Value
from django.db.models.functions import Coalesce
from graphene_django import DjangoObjectType

from orders.models import Order
from products.models import Category, Product, Review
from users.models import User


class CategoryType(DjangoObjectType):
    """GraphQL type for product categories."""

    class Meta:
        model = Category
        fields = ("id", "name", "name_en", "slug", "parent")


class ReviewType(DjangoObjectType):
    """GraphQL type for product reviews."""

    user_email = graphene.String()

    class Meta:
        model = Review
        fields = ("id", "rating", "comment", "comment_en", "created_at")

    def resolve_user_email(self, info) -> str:
        return self.user.email


class ProductType(DjangoObjectType):
    """GraphQL type for catalog products."""

    in_stock = graphene.Boolean()
    sold_units = graphene.Int()

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "name_en",
            "slug",
            "description",
            "description_en",
            "price",
            "category",
            "stock",
            "is_active",
            "created_at",
            "updated_at",
            "reviews",
        )

    def resolve_in_stock(self, info) -> bool:
        return self.in_stock

    def resolve_sold_units(self, info) -> int:
        return int(getattr(self, "sold_units", 0) or 0)


class OrderAnalyticsType(graphene.ObjectType):
    """Aggregate order metrics for analytics."""

    order_count = graphene.Int()
    paid_order_count = graphene.Int()
    revenue = graphene.Decimal()
    average_check = graphene.Decimal()


class UserActivityType(graphene.ObjectType):
    """Per-user purchase activity."""

    email = graphene.String()
    order_count = graphene.Int()
    total_spent = graphene.Decimal()
    is_repeat_buyer = graphene.Boolean()


class Query(graphene.ObjectType):
    """Root GraphQL queries for catalog and analytics."""

    categories = graphene.List(CategoryType)
    products = graphene.List(
        ProductType,
        q=graphene.String(required=False),
        category=graphene.String(required=False),
        active_only=graphene.Boolean(required=False, default_value=True),
    )
    product = graphene.Field(ProductType, slug=graphene.String(required=True))
    order_analytics = graphene.Field(OrderAnalyticsType)
    popular_products = graphene.List(
        ProductType,
        limit=graphene.Int(required=False, default_value=5),
    )
    low_stock_products = graphene.List(
        ProductType,
        threshold=graphene.Int(required=False, default_value=5),
    )
    user_activity = graphene.List(
        UserActivityType,
        limit=graphene.Int(required=False, default_value=10),
    )

    def resolve_categories(self, info):
        return Category.objects.all()

    def resolve_products(
        self,
        info,
        q: str | None = None,
        category: str | None = None,
        active_only: bool = True,
    ):
        qs = Product.objects.select_related("category").prefetch_related("reviews")
        if active_only:
            qs = qs.filter(is_active=True)
        if q:
            qs = qs.filter(
                Q(name__icontains=q)
                | Q(name_en__icontains=q)
                | Q(description__icontains=q)
                | Q(description_en__icontains=q)
            )
        if category:
            qs = qs.filter(category__slug=category)
        return qs

    def resolve_product(self, info, slug: str):
        return (
            Product.objects.filter(slug=slug, is_active=True)
            .select_related("category")
            .prefetch_related("reviews")
            .first()
        )

    def resolve_order_analytics(self, info) -> OrderAnalyticsType:
        paid = Order.objects.filter(status__in=Order.PAID_STATUSES)
        revenue = paid.aggregate(
            total=Coalesce(
                Sum("total_price"),
                Value(Decimal("0"), output_field=DecimalField(max_digits=12, decimal_places=2)),
            )
        )["total"]
        average = paid.aggregate(
            avg=Coalesce(
                Avg("total_price"),
                Value(Decimal("0"), output_field=DecimalField(max_digits=12, decimal_places=2)),
            )
        )["avg"]
        return OrderAnalyticsType(
            order_count=Order.objects.count(),
            paid_order_count=paid.count(),
            revenue=revenue,
            average_check=average,
        )

    def resolve_popular_products(self, info, limit: int = 5):
        return (
            Product.objects.annotate(
                sold_units=Coalesce(Sum("order_items__quantity"), Value(0)),
            )
            .filter(sold_units__gt=0)
            .order_by("-sold_units", "name")[: max(1, min(limit, 50))]
        )

    def resolve_low_stock_products(self, info, threshold: int = 5):
        return (
            Product.objects.filter(is_active=True, stock__lte=max(0, threshold))
            .select_related("category")
            .order_by("stock", "name")
        )

    def resolve_user_activity(self, info, limit: int = 10):
        users = (
            User.objects.annotate(
                order_count=Count("orders", distinct=True),
                total_spent=Coalesce(
                    Sum(
                        "orders__total_price",
                        filter=Q(orders__status__in=Order.PAID_STATUSES),
                    ),
                    Value(Decimal("0"), output_field=DecimalField(max_digits=12, decimal_places=2)),
                ),
            )
            .filter(order_count__gt=0)
            .order_by("-order_count", "-total_spent")[: max(1, min(limit, 50))]
        )
        return [
            UserActivityType(
                email=user.email,
                order_count=user.order_count,
                total_spent=user.total_spent,
                is_repeat_buyer=user.order_count > 1,
            )
            for user in users
        ]


schema = graphene.Schema(query=Query)
