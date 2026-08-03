from django.urls import path

from .views import ProductListView, ProductDetailView

app_name = "products"

urlpatterns = [
    path("products/", ProductListView.as_view(), name="list"),
    path("product/<slug:slug>/", ProductDetailView.as_view(), name="detail"),
]
