from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from orders.models import Order, OrderItem
from products.models import Category, Product, Review

User = get_user_model()


@pytest.fixture
def product(db) -> Product:
    cat = Category.objects.create(name="Hops", slug="hops")
    return Product.objects.create(
        name="Citra Hops", slug="citra-hops", description="Tropical aroma",
        price=Decimal("5.99"), category=cat, stock=5,
    )


@pytest.fixture
def buyer(product: Product):
    """A user with a delivered order containing the product."""
    user = User.objects.create_user(email="buyer@example.com", password="pass12345")
    order = Order.objects.create(
        user=user, status=Order.Status.DELIVERED, full_name="B", phone="1",
        city="Kyiv", address="x",
    )
    OrderItem.objects.create(order=order, product=product, quantity=1, price=product.price)
    return user


@pytest.mark.django_db
class TestProductDetail:
    def test_page_renders(self, client, product: Product) -> None:
        response = client.get(product.get_absolute_url())
        assert response.status_code == 200
        html = response.content.decode()
        assert "Citra Hops" in html and "Додати в кошик" in html
        assert "img/products/citra_hops.jpg" in html

    def test_shows_reviews(self, client, product: Product, buyer) -> None:
        Review.objects.create(product=product, user=buyer, rating=4, comment="Nice hop!")
        html = client.get(product.get_absolute_url()).content.decode()
        assert "Nice hop!" in html

    def test_review_requires_purchase(self, client, product: Product) -> None:
        user = User.objects.create_user(email="new@example.com", password="pass12345")
        client.force_login(user)
        client.post(product.get_absolute_url(), {"rating": 5, "comment": "Fake"})
        assert Review.objects.count() == 0

    def test_buyer_can_review_once(self, client, product: Product, buyer) -> None:
        client.force_login(buyer)
        response = client.get(product.get_absolute_url())
        assert response.context["review_state"] == "can_review"
        assert "Залишити відгук" in response.content.decode()

        response = client.post(
            product.get_absolute_url(), {"rating": 5, "comment": "Great"}, follow=True
        )
        assert response.status_code == 200
        assert Review.objects.filter(product=product, user=buyer).count() == 1
        assert response.context["review_state"] == "already_reviewed"
        assert "Ви вже залишили відгук" in response.content.decode()
        client.post(product.get_absolute_url(), {"rating": 1, "comment": "Again"})
        assert Review.objects.filter(product=product, user=buyer).count() == 1

    def test_guest_sees_review_sign_in_hint(self, client, product: Product) -> None:
        html = client.get(product.get_absolute_url()).content.decode()
        assert "Увійдіть, щоб залишити відгук" in html

    def test_pending_cod_order_allows_review(self, client, product: Product) -> None:
        user = User.objects.create_user(email="cod@example.com", password="pass12345")
        order = Order.objects.create(
            user=user,
            status=Order.Status.PENDING,
            full_name="C",
            phone="1",
            city="Kyiv",
            address="x",
            payment_method=Order.PaymentMethod.COD,
        )
        OrderItem.objects.create(order=order, product=product, quantity=1, price=product.price)
        client.force_login(user)
        response = client.get(product.get_absolute_url())
        assert response.context["review_state"] == "can_review"

    def test_anonymous_review_redirects_to_login(self, client, product: Product) -> None:
        response = client.post(product.get_absolute_url(), {"rating": 5, "comment": "x"})
        assert response.status_code == 302
        assert "login" in response.url
