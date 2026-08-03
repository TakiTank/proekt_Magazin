"""DRF serializers for products, cart, orders and accounts."""

from typing import Any

from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from config.context_processors import site_ui
from orders.cart import Cart
from orders.emails import send_order_emails
from orders.models import Order, OrderItem
from orders.services import create_order
from products.models import Category, Product, Review
from products.services import user_has_purchased
from users.models import User


class CategorySerializer(serializers.ModelSerializer):
    """Category data for product responses."""

    class Meta:
        model = Category
        fields = ["id", "name", "name_en", "slug", "parent"]


class ReviewSerializer(serializers.ModelSerializer):
    """Read-only review representation."""

    user = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model = Review
        fields = ["id", "user", "rating", "comment", "comment_en", "created_at"]


class ReviewCreateSerializer(serializers.ModelSerializer):
    """Write serializer that enforces purchase-gated reviews."""

    class Meta:
        model = Review
        fields = ["rating", "comment"]

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        request = self.context["request"]
        product: Product = self.context["product"]
        ui = site_ui(request)["ui"]
        if not user_has_purchased(request.user, product):
            raise serializers.ValidationError(ui["review_purchase_required"])
        if Review.objects.filter(product=product, user=request.user).exists():
            raise serializers.ValidationError(ui["review_duplicate"])
        return attrs

    def create(self, validated_data: dict[str, Any]) -> Review:
        return Review.objects.create(
            product=self.context["product"],
            user=self.context["request"].user,
            **validated_data,
        )


class ProductSerializer(serializers.ModelSerializer):
    """Public product listing data."""

    category = CategorySerializer(read_only=True)
    avg_rating = serializers.FloatField(read_only=True, allow_null=True)
    review_count = serializers.IntegerField(read_only=True)
    sold = serializers.IntegerField(read_only=True)
    in_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "name_en",
            "slug",
            "description",
            "description_en",
            "price",
            "category",
            "image",
            "stock",
            "is_active",
            "avg_rating",
            "review_count",
            "sold",
            "in_stock",
            "created_at",
            "updated_at",
        ]


class ProductDetailSerializer(ProductSerializer):
    """Detailed product payload with nested reviews."""

    reviews = ReviewSerializer(many=True, read_only=True)

    class Meta(ProductSerializer.Meta):
        fields = ProductSerializer.Meta.fields + ["reviews"]


class CartLineSerializer(serializers.Serializer):
    """One cart line with the live product data."""

    product = ProductSerializer(read_only=True)
    quantity = serializers.IntegerField()
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2)


class CartSerializer(serializers.Serializer):
    """Shopping cart payload returned by the API."""

    items = CartLineSerializer(many=True)
    total_quantity = serializers.IntegerField()
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2)


class CartMutationSerializer(serializers.Serializer):
    """Input payload for cart operations."""

    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, required=False, default=1)


class OrderItemSerializer(serializers.ModelSerializer):
    """Read-only order line representation."""

    product = ProductSerializer(read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "product", "quantity", "price", "total_price"]
        read_only_fields = fields


class OrderSerializer(serializers.ModelSerializer):
    """Read-only order data with nested items."""

    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "status",
            "full_name",
            "phone",
            "city",
            "address",
            "payment_method",
            "total_price",
            "created_at",
            "updated_at",
            "items",
        ]


class OrderCreateSerializer(serializers.ModelSerializer):
    """Create an order from the session cart."""

    class Meta:
        model = Order
        fields = ["full_name", "phone", "city", "address", "payment_method"]

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        cart: Cart = self.context["cart"]
        if len(cart) == 0:
            request = self.context["request"]
            raise serializers.ValidationError(site_ui(request)["ui"]["api_cart_empty"])
        return attrs

    def create(self, validated_data: dict[str, Any]) -> Order:
        request = self.context["request"]
        cart: Cart = self.context["cart"]
        order = create_order(request.user, cart, **validated_data)
        send_order_emails(order)
        cart.clear()
        return order


class OrderStatusSerializer(serializers.ModelSerializer):
    """Status updates from the API, limited to cancellations."""

    class Meta:
        model = Order
        fields = ["status"]

    def validate_status(self, value: str) -> str:
        if value != Order.Status.CANCELLED:
            request = self.context["request"]
            raise serializers.ValidationError(site_ui(request)["ui"]["api_cancellation_only"])
        return value


class UserRegisterSerializer(serializers.ModelSerializer):
    """Create a user account for the API."""

    password = serializers.CharField(write_only=True, trim_whitespace=False)

    class Meta:
        model = User
        fields = [
            "email",
            "password",
            "first_name",
            "last_name",
            "phone",
            "city",
            "address",
        ]

    def validate_password(self, value: str) -> str:
        validate_password(value, user=User(email=self.initial_data.get("email", "")))
        return value

    def create(self, validated_data: dict[str, Any]) -> User:
        password = validated_data.pop("password")
        return User.objects.create_user(password=password, **validated_data)


class UserProfileSerializer(serializers.ModelSerializer):
    """Personal account representation used by /api/users/me/."""

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "phone", "city", "address"]
        read_only_fields = ["email"]
