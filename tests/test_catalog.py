from decimal import Decimal

import pytest
from django.urls import reverse

from products.models import Category, Product


@pytest.fixture
def catalog(db):
    hops = Category.objects.create(name="Hops", slug="hops")
    malts = Category.objects.create(name="Malts", slug="malts")
    cheap = Product.objects.create(
        name="Saaz Hops", slug="saaz-hops", description="Noble aroma hop",
        price=Decimal("5.49"), category=hops, stock=10,
    )
    dear = Product.objects.create(
        name="Maris Otter Malt", slug="maris-otter", description="Rich biscuit base malt",
        price=Decimal("14.99"), category=malts, stock=3,
    )
    return {"hops": hops, "malts": malts, "cheap": cheap, "dear": dear}


@pytest.mark.django_db
class TestCatalog:
    def test_home_and_products_show_catalog(self, client, catalog) -> None:
        for url in (reverse("home"), reverse("products:list")):
            response = client.get(url)
            assert response.status_code == 200
            assert "Saaz Hops" in response.content.decode()
            assert "img/products/" in response.content.decode()

    def test_search_by_name_and_description(self, client, catalog) -> None:
        html = client.get(reverse("home"), {"q": "biscuit"}).content.decode()
        assert "Maris Otter" in html and "Saaz" not in html

    def test_filter_by_category(self, client, catalog) -> None:
        html = client.get(reverse("home"), {"category": "hops"}).content.decode()
        assert "Saaz" in html and "Maris Otter" not in html

    def test_filter_by_price_range(self, client, catalog) -> None:
        html = client.get(reverse("home"), {"price_min": "10"}).content.decode()
        assert "Maris Otter" in html and "Saaz" not in html

    def test_sort_by_price(self, client, catalog) -> None:
        response = client.get(reverse("home"), {"sort": "price_desc"})
        products = list(response.context["products"])
        assert products[0].name == "Maris Otter Malt"

    def test_inactive_product_hidden(self, client, catalog) -> None:
        catalog["cheap"].is_active = False
        catalog["cheap"].save()
        assert "Saaz" not in client.get(reverse("home")).content.decode()

    def test_pagination(self, client, catalog) -> None:
        for i in range(10):
            Product.objects.create(
                name=f"Filler {i}", slug=f"filler-{i}", description="x",
                price=Decimal("1.00"), category=catalog["hops"], stock=1,
            )
        response = client.get(reverse("home"))
        assert response.context["paginator"].num_pages == 2
        assert len(response.context["products"]) == 8
