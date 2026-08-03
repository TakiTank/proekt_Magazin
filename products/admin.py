"""Admin customisation for catalog models."""

from __future__ import annotations

from decimal import Decimal

from django.contrib import admin, messages
from django.db.models import Count, DecimalField, F, Sum
from django.db.models.functions import Coalesce
from config.admin_metrics import product_analytics

from .models import Category, Product, Review


class StockStatusFilter(admin.SimpleListFilter):
    title = "stock"
    parameter_name = "stock_status"

    def lookups(self, request, model_admin):
        return (
            ("in_stock", "In stock"),
            ("low", "Low stock"),
            ("out", "Out of stock"),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == "in_stock":
            return queryset.filter(stock__gt=0)
        if value == "low":
            return queryset.filter(stock__gt=0, stock__lte=5)
        if value == "out":
            return queryset.filter(stock=0)
        return queryset


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "name_en", "slug", "parent", "product_count", "updated_at")
    search_fields = ("name", "name_en", "slug")
    list_filter = ("parent",)
    prepopulated_fields = {"slug": ("name",)}
    fields = ("name", "name_en", "slug", "parent")

    @admin.display(ordering="product_count", description="Products")
    def product_count(self, obj: Category) -> int:
        return getattr(obj, "product_count", obj.products.count())

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(product_count=Count("products"))


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    change_list_template = "admin/change_list_metrics.html"
    list_display = (
        "name",
        "category",
        "price",
        "stock",
        "is_active",
        "sold_units_display",
        "orders_count_display",
        "revenue_display",
    )
    list_filter = ("category", "is_active", StockStatusFilter)
    search_fields = ("name", "name_en", "description", "description_en", "slug", "category__name")
    list_select_related = ("category",)
    prepopulated_fields = {"slug": ("name",)}
    fields = (
        "name",
        "name_en",
        "slug",
        "description",
        "description_en",
        "price",
        "category",
        "image",
        "is_active",
        "stock",
    )
    actions = ["make_active", "make_inactive"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("category").annotate(
            sold_units=Coalesce(Sum("order_items__quantity"), 0),
            orders_count=Coalesce(Count("order_items__order", distinct=True), 0),
            revenue=Coalesce(
                Sum(
                    F("order_items__quantity") * F("order_items__price"),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                ),
                Decimal("0"),
            ),
            review_count=Coalesce(Count("reviews", distinct=True), 0),
        )

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context.update(product_analytics())
        return super().changelist_view(request, extra_context=extra_context)

    @admin.display(ordering="sold_units", description="Sold")
    def sold_units_display(self, obj: Product) -> int:
        return getattr(obj, "sold_units", 0)

    @admin.display(ordering="orders_count", description="Orders")
    def orders_count_display(self, obj: Product) -> int:
        return getattr(obj, "orders_count", 0)

    @admin.display(ordering="revenue", description="Revenue")
    def revenue_display(self, obj: Product) -> str:
        revenue = getattr(obj, "revenue", Decimal("0"))
        return f"${revenue:.2f}"

    @admin.action(description="Mark selected products as active")
    def make_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} product(s) marked active.", messages.SUCCESS)

    @admin.action(description="Mark selected products as inactive")
    def make_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} product(s) marked inactive.", messages.SUCCESS)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("product", "user", "rating", "created_at")
    list_filter = ("rating", "created_at")
    search_fields = ("product__name", "user__email", "comment", "comment_en")
    list_select_related = ("product", "user")
    fields = ("product", "user", "rating", "comment", "comment_en")
