"""URL routes for the REST API and documentation."""

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CartAPIView,
    LoginAPIView,
    MeAPIView,
    OrderViewSet,
    ProductViewSet,
    RefreshAPIView,
    RegisterAPIView,
)

router = DefaultRouter()
router.register("products", ProductViewSet, basename="products")
router.register("orders", OrderViewSet, basename="orders")

app_name = "api"

urlpatterns = [
    path("", include(router.urls)),
    path("cart/", CartAPIView.as_view(), name="cart"),
    path("users/register/", RegisterAPIView.as_view(), name="register"),
    path("users/login/", LoginAPIView.as_view(), name="login"),
    path("users/refresh/", RefreshAPIView.as_view(), name="refresh"),
    path("users/me/", MeAPIView.as_view(), name="me"),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "docs/",
        SpectacularSwaggerView.as_view(url_name="api:schema"),
        name="docs",
    ),
]
