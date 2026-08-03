"""REST API views."""

from django.shortcuts import get_object_or_404
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from orders.cart import Cart, CartQuantityError
from orders.models import Order
from orders.services import InsufficientStock
from products.models import Product
from config.context_processors import site_ui

from .serializers import (
    CartMutationSerializer,
    CartSerializer,
    OrderCreateSerializer,
    OrderSerializer,
    OrderStatusSerializer,
    ProductDetailSerializer,
    ProductSerializer,
    ReviewCreateSerializer,
    ReviewSerializer,
    UserProfileSerializer,
    UserRegisterSerializer,
)
from .services import build_product_queryset, cart_snapshot, filter_products


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """Browse products and post purchase-gated reviews."""

    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = "slug"

    def get_queryset(self):
        queryset = build_product_queryset()
        if self.action in {"retrieve", "reviews"}:
            queryset = queryset.prefetch_related("reviews__user")
        return filter_products(queryset, self.request.query_params)

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ProductDetailSerializer
        return ProductSerializer

    @action(detail=True, methods=["get", "post"])
    def reviews(self, request, slug: str | None = None):
        """List reviews or create a new one for the given product."""
        product = self.get_object()
        if request.method == "GET":
            serializer = ReviewSerializer(product.reviews.select_related("user"), many=True)
            return Response(serializer.data)

        serializer = ReviewCreateSerializer(
            data=request.data,
            context={"request": request, "product": product},
        )
        serializer.is_valid(raise_exception=True)
        review = serializer.save()
        return Response(ReviewSerializer(review).data, status=status.HTTP_201_CREATED)


class CartAPIView(APIView):
    """Session-backed cart endpoint."""

    permission_classes = [AllowAny]

    def get(self, request):
        return Response(CartSerializer(cart_snapshot(Cart(request))).data)

    def post(self, request):
        cart = Cart(request)
        site = site_ui(request)
        ui = site["ui"]
        serializer = CartMutationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = self._get_product(serializer.validated_data["product_id"])
        try:
            cart.add(product, serializer.validated_data["quantity"])
        except CartQuantityError as exc:
            return Response(
                {
                    "detail": ui["api_item_unavailable"].format(
                        available=exc.available,
                        product=product.localized_name(site["site_language"]),
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(CartSerializer(cart_snapshot(cart)).data, status=status.HTTP_200_OK)

    def patch(self, request):
        cart = Cart(request)
        site = site_ui(request)
        ui = site["ui"]
        serializer = CartMutationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = self._get_product(serializer.validated_data["product_id"])
        try:
            cart.set_quantity(product, serializer.validated_data["quantity"])
        except CartQuantityError as exc:
            return Response(
                {
                    "detail": ui["api_item_unavailable"].format(
                        available=exc.available,
                        product=product.localized_name(site["site_language"]),
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(CartSerializer(cart_snapshot(cart)).data)

    def delete(self, request):
        cart = Cart(request)
        product = self._get_product_from_request(request)
        cart.remove(product)
        return Response(CartSerializer(cart_snapshot(cart)).data)

    def _get_product(self, product_id: int) -> Product:
        return get_object_or_404(Product, pk=product_id, is_active=True)

    def _get_product_from_request(self, request) -> Product:
        product_id = request.data.get("product_id") or request.query_params.get("product_id")
        if not product_id:
            raise ValidationError({"product_id": "This field is required."})
        return self._get_product(int(product_id))


class OrderViewSet(viewsets.ModelViewSet):
    """Create, list and cancel user orders."""

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related("items__product")

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        if self.action in {"update", "partial_update"}:
            return OrderStatusSerializer
        return OrderSerializer

    def create(self, request, *args, **kwargs):
        ui = site_ui(request)["ui"]
        serializer = self.get_serializer(
            data=request.data,
            context={"request": request, "cart": Cart(request)},
        )
        serializer.is_valid(raise_exception=True)
        try:
            order = serializer.save()
        except InsufficientStock as exc:
            raise ValidationError(
                {
                    "detail": ui["api_item_unavailable"].format(
                        available=exc.available,
                        product=exc.product.localized_name(site_ui(request)["site_language"]),
                    )
                }
            ) from exc
        output = OrderSerializer(order, context=self.get_serializer_context())
        headers = self.get_success_headers(output.data)
        return Response(output.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_update(self, serializer):
        order = self.get_object()
        ui = site_ui(self.request)["ui"]
        if order.status in {Order.Status.CANCELLED, Order.Status.DELIVERED}:
            raise ValidationError({"detail": ui["api_order_locked"]})
        serializer.save(status=Order.Status.CANCELLED)

    def destroy(self, request, *args, **kwargs):
        order = self.get_object()
        ui = site_ui(request)["ui"]
        if order.status in {Order.Status.CANCELLED, Order.Status.DELIVERED}:
            return Response(
                {"detail": ui["api_order_locked"]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        order.status = Order.Status.CANCELLED
        order.save(update_fields=["status"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class RegisterAPIView(generics.CreateAPIView):
    """Create a new account for JWT/API usage."""

    permission_classes = [AllowAny]
    serializer_class = UserRegisterSerializer


class MeAPIView(generics.RetrieveUpdateAPIView):
    """Read or update the current user's profile."""

    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user


class LoginAPIView(TokenObtainPairView):
    """JWT login endpoint."""


class RefreshAPIView(TokenRefreshView):
    """JWT refresh endpoint."""
