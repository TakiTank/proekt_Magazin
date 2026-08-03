from django.apps import AppConfig


class ProductsConfig(AppConfig):
    """Catalog: categories, products, reviews."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "products"
