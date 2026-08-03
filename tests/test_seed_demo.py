import json

import pytest
from django.core.management import call_command
from django.urls import reverse

from products.models import Category, Product, Review


@pytest.mark.django_db
def test_seed_demo_creates_ukrainian_catalog_orders_items_and_reviews() -> None:
    call_command("seed_demo")

    hops = Category.objects.get(slug="hops")
    assert hops.name == "Хміль"
    assert hops.name_en == "Hops"

    product = Product.objects.get(slug="citra-hops")
    assert product.name == "Цитра хміль"
    assert product.name_en == "Citra hops"
    assert product.description_en


@pytest.mark.django_db
def test_seed_demo_repairs_partially_seeded_database() -> None:
    from orders.models import OrderItem

    call_command("seed_demo")
    OrderItem.objects.all().delete()
    Review.objects.all().delete()

    call_command("seed_demo")

    assert OrderItem.objects.count() > 0
    assert Review.objects.count() > 0


@pytest.mark.django_db
def test_english_catalog_uses_translated_product_content(client) -> None:
    call_command("seed_demo")
    client.post(reverse("set_language", args=["en"]), {"next": "/"})
    html = client.get(reverse("home"), {"q": "citra"}).content.decode()
    assert "Hops" in html
    assert "Citra hops" in html
    assert "Хміль" not in html
    assert "Цитра хміль" not in html


@pytest.mark.django_db
def test_graphql_products_and_categories(client) -> None:
    call_command("seed_demo")
    query = """
    {
      categories { slug name nameEn }
      products(q: "citra") { slug name nameEn inStock category { slug } }
      product(slug: "citra-hops") { nameEn descriptionEn }
    }
    """
    response = client.post(
        "/graphql/",
        data=json.dumps({"query": query}),
        content_type="application/json",
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload
    data = payload["data"]
    assert any(item["slug"] == "hops" and item["nameEn"] == "Hops" for item in data["categories"])
    assert data["products"][0]["slug"] == "citra-hops"
    assert data["product"]["nameEn"] == "Citra hops"


@pytest.mark.django_db
def test_graphql_analytics(client) -> None:
    call_command("seed_demo")
    query = """
    {
      orderAnalytics { orderCount paidOrderCount revenue averageCheck }
      popularProducts(limit: 3) { slug soldUnits }
      userActivity(limit: 3) { email orderCount isRepeatBuyer }
    }
    """
    response = client.post(
        "/graphql/",
        data=json.dumps({"query": query}),
        content_type="application/json",
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload
    assert payload["data"]["orderAnalytics"]["orderCount"] >= 1
    assert len(payload["data"]["popularProducts"]) >= 1
    assert len(payload["data"]["userActivity"]) >= 1
