from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from orders.models import Order, OrderItem
from products.models import Category, Product

User = get_user_model()


@pytest.fixture
def superuser(db):
    return User.objects.create_superuser(email="admin@example.com", password="admin12345")


@pytest.fixture
def staff_user(db):
    return User.objects.create_user(
        email="staff@example.com", password="staff12345", is_staff=True
    )


@pytest.fixture
def catalog(db):
    category = Category.objects.create(name="Hops", slug="hops")
    product_a = Product.objects.create(
        name="Citra",
        slug="citra",
        description="d",
        price=Decimal("5.99"),
        category=category,
        stock=8,
    )
    product_b = Product.objects.create(
        name="Cascade",
        slug="cascade",
        description="d",
        price=Decimal("4.99"),
        category=category,
        stock=2,
    )
    customer = User.objects.create_user(email="buyer@example.com", password="pass12345")
    order = Order.objects.create(
        user=customer,
        status=Order.Status.PAID,
        full_name="Buyer",
        phone="+380501112233",
        city="Kyiv",
        address="Khreshchatyk 1",
        total_price=Decimal("0"),
    )
    OrderItem.objects.create(order=order, product=product_a, quantity=2, price=product_a.price)
    OrderItem.objects.create(order=order, product=product_b, quantity=1, price=product_b.price)
    order.total_price = Decimal("16.97")
    order.save(update_fields=["total_price"])
    return product_a, product_b, order


@pytest.mark.django_db
def test_product_admin_shows_metrics_and_top_products(client, superuser, catalog) -> None:
    product_a, _, _ = catalog
    client.force_login(superuser)
    response = client.get(reverse("admin:products_product_changelist"))
    assert response.status_code == 200
    html = response.content.decode()
    assert "Catalog analytics" in html
    assert "Top products" in html
    assert "Active products" in html
    assert "Citra" in html
    assert str(product_a.stock) in html


@pytest.mark.django_db
def test_product_admin_action_changes_status(client, superuser, catalog) -> None:
    product_a, _, _ = catalog
    client.force_login(superuser)
    response = client.post(
        reverse("admin:products_product_changelist"),
        {"action": "make_inactive", "_selected_action": [str(product_a.pk)]},
        follow=True,
    )
    assert response.status_code == 200
    product_a.refresh_from_db()
    assert product_a.is_active is False


@pytest.mark.django_db
def test_order_admin_shows_revenue_and_actions(client, superuser, catalog) -> None:
    _, _, order = catalog
    client.force_login(superuser)
    response = client.get(reverse("admin:orders_order_changelist"))
    assert response.status_code == 200
    html = response.content.decode()
    assert "Order analytics" in html
    assert "Revenue" in html
    assert "Top products by sales" in html
    assert "Citra" in html

    response = client.post(
        reverse("admin:orders_order_changelist"),
        {"action": "mark_cancelled", "_selected_action": [str(order.pk)]},
        follow=True,
    )
    assert response.status_code == 200
    order.refresh_from_db()
    assert order.status == Order.Status.CANCELLED


@pytest.mark.django_db
def test_staff_cannot_access_user_admin(client, staff_user) -> None:
    client.force_login(staff_user)
    response = client.get(reverse("admin:users_user_changelist"))
    assert response.status_code == 403


@pytest.mark.django_db
def test_superuser_can_access_user_admin(client, superuser) -> None:
    client.force_login(superuser)
    response = client.get(reverse("admin:users_user_changelist"))
    assert response.status_code == 200
