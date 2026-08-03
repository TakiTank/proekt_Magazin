from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from products.models import Category, Product, Review

User = get_user_model()


@pytest.fixture
def category(db) -> Category:
    return Category.objects.create(name="Hops", slug="hops")


@pytest.fixture
def product(category: Category) -> Product:
    return Product.objects.create(
        name="Citra Hops", slug="citra-hops", description="Citrus bomb",
        price=Decimal("5.99"), category=category, stock=10,
    )


@pytest.mark.django_db
class TestProductModels:
    def test_str_and_url(self, product: Product) -> None:
        assert str(product) == "Citra Hops"
        assert product.get_absolute_url() == "/product/citra-hops/"

    def test_in_stock(self, product: Product) -> None:
        assert product.in_stock
        product.stock = 0
        assert not product.in_stock

    def test_nested_categories(self, category: Category) -> None:
        child = Category.objects.create(name="Aroma Hops", slug="aroma-hops", parent=category)
        assert child.parent == category
        assert list(category.children.all()) == [child]

    def test_review_unique_per_user(self, product: Product) -> None:
        user = User.objects.create_user(email="r@r.com", password="x")
        Review.objects.create(product=product, user=user, rating=5, comment="Great")
        with pytest.raises(IntegrityError):
            Review.objects.create(product=product, user=user, rating=1, comment="Dup")
