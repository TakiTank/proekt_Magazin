"""Admin customisation for orders."""

from __future__ import annotations

from django.contrib import admin, messages
from django.db.models import Count

from config.admin_metrics import order_analytics

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "quantity", "price")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    change_list_template = "admin/change_list_metrics.html"
    list_display = (
        "id",
        "user",
        "status",
        "payment_method",
        "total_price",
        "item_count_display",
        "created_at",
    )
    list_filter = ("status", "payment_method", "created_at")
    search_fields = ("id", "user__email", "full_name", "phone", "city", "address")
    list_select_related = ("user",)
    date_hierarchy = "created_at"
    inlines = [OrderItemInline]
    actions = ["mark_paid", "mark_shipped", "mark_delivered", "mark_cancelled"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user").annotate(
            item_count=Count("items")
        )

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context.update(order_analytics())
        return super().changelist_view(request, extra_context=extra_context)

    @admin.display(ordering="item_count", description="Items")
    def item_count_display(self, obj: Order) -> int:
        return getattr(obj, "item_count", obj.items.count())

    @admin.action(description="Mark selected orders as paid")
    def mark_paid(self, request, queryset):
        updated = queryset.update(status=Order.Status.PAID)
        self.message_user(request, f"{updated} order(s) marked paid.", messages.SUCCESS)

    @admin.action(description="Mark selected orders as shipped")
    def mark_shipped(self, request, queryset):
        updated = queryset.update(status=Order.Status.SHIPPED)
        self.message_user(request, f"{updated} order(s) marked shipped.", messages.SUCCESS)

    @admin.action(description="Mark selected orders as delivered")
    def mark_delivered(self, request, queryset):
        updated = queryset.update(status=Order.Status.DELIVERED)
        self.message_user(request, f"{updated} order(s) marked delivered.", messages.SUCCESS)

    @admin.action(description="Cancel selected orders")
    def mark_cancelled(self, request, queryset):
        updated = queryset.update(status=Order.Status.CANCELLED)
        self.message_user(request, f"{updated} order(s) cancelled.", messages.SUCCESS)
