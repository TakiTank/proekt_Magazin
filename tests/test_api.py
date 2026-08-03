from decimal import Decimal

import pytest
from django.core import mail
from django.urls import reverse
from rest_framework.test import APIClient

from orders.models import Order, OrderItem
from products.models import Category, Product, Review
from users.models import User


@pytest.fixture
def api_client() -> APIClient:
    """DRF client with session support."""
    return APIClient()


@pytest.fixture
def category(db) -> Category:
    return Category.objects.create(name="Hops", slug="hops")


@pytest.fixture
def product(category: Category) -> Product:
    return Product.objects.create(
        name="Citra Hops",
        slug="citra-hops",
        description="Tropical aroma hop",
        price=Decimal("5.99"),
        category=category,
        stock=5,
    )


@pytest.fixture
def buyer(db, product: Product) -> User:
    user = User.objects.create_user(
        email="buyer@example.com",
        password="strong-pass-123",
        first_name="Ira",
        last_name="Brewer",
    )
    order = Order.objects.create(
        user=user,
        status=Order.Status.DELIVERED,
        full_name="Ira Brewer",
        phone="+380501112233",
        city="Kyiv",
        address="Khreshchatyk 1",
        payment_method=Order.PaymentMethod.DEBIT,
    )
    OrderItem.objects.create(order=order, product=product, quantity=1, price=product.price)
    return user


@pytest.mark.django_db
class TestApi:
    def test_product_list_search_and_pagination(
        self, api_client: APIClient, product: Product
    ) -> None:
        response = api_client.get(reverse("api:products-list"), {"q": "tropical"})
        assert response.status_code == 200
        assert response.data["count"] == 1
        assert response.data["results"][0]["name"] == product.name

    def test_register_login_and_me(self, api_client: APIClient) -> None:
        register = api_client.post(
            reverse("api:register"),
            {
                "email": "api@example.com",
                "password": "strong-pass-123",
                "first_name": "Api",
                "last_name": "User",
            },
            format="json",
        )
        assert register.status_code == 201

        login = api_client.post(
            reverse("api:login"),
            {"email": "api@example.com", "password": "strong-pass-123"},
            format="json",
        )
        assert login.status_code == 200
        assert "access" in login.data and "refresh" in login.data

        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        me = api_client.get(reverse("api:me"))
        assert me.status_code == 200
        assert me.data["email"] == "api@example.com"

    def test_cart_and_order_flow(self, api_client: APIClient, product: Product) -> None:
        user = User.objects.create_user(email="shopper@example.com", password="strong-pass-123")

        cart_add = api_client.post(
            reverse("api:cart"),
            {"product_id": product.pk, "quantity": 2},
            format="json",
        )
        assert cart_add.status_code == 200
        assert cart_add.data["total_quantity"] == 2

        login = api_client.post(
            reverse("api:login"),
            {"email": user.email, "password": "strong-pass-123"},
            format="json",
        )
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

        order = api_client.post(
            reverse("api:orders-list"),
            {
                "full_name": "Shop Per",
                "phone": "+380501112233",
                "city": "Kyiv",
                "address": "Khreshchatyk 1",
                "payment_method": "debit",
            },
            format="json",
        )
        assert order.status_code == 201
        assert order.data["total_price"] == "11.98"

        created = Order.objects.get(user=user)
        assert created.status == Order.Status.PAID
        assert created.total_price == Decimal("11.98")
        product.refresh_from_db()
        assert product.stock == 3
        assert len(mail.outbox) == 2
        assert api_client.get(reverse("api:cart")).data["total_quantity"] == 0

    def test_review_gated_by_purchase(
        self, api_client: APIClient, buyer: User, product: Product
    ) -> None:
        login = api_client.post(
            reverse("api:login"),
            {"email": buyer.email, "password": "strong-pass-123"},
            format="json",
        )
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        url = reverse("api:products-reviews", args=[product.slug])

        review = api_client.post(url, {"rating": 5, "comment": "Great"}, format="json")
        assert review.status_code == 201
        assert Review.objects.filter(product=product, user=buyer).count() == 1

        other = User.objects.create_user(email="other@example.com", password="strong-pass-123")
        login = api_client.post(
            reverse("api:login"),
            {"email": other.email, "password": "strong-pass-123"},
            format="json",
        )
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        denied = api_client.post(url, {"rating": 4, "comment": "Nope"}, format="json")
        assert denied.status_code == 400
