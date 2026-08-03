"""Idempotent demo data: products, demo users, orders, order items and reviews."""

from decimal import Decimal
from typing import Any

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from orders.models import Order, OrderItem
from products.models import Category, Product, Review

CATEGORIES = [
    ("hops", "Хміль", "Hops"),
    ("malts", "Солод", "Malts"),
    ("yeast", "Дріжджі", "Yeast"),
    ("adjuncts", "Додатки", "Adjuncts"),
    ("kits", "Набори", "Kits"),
]

PRODUCTS = [
    (
        "Цитра хміль",
        "Citra hops",
        "citra-hops",
        "hops",
        "5.99",
        25,
        "Яскравий цитрусовий і тропічний аромат для hazy IPA.",
        "Bright citrus and tropical aroma for hazy IPA.",
    ),
    (
        "Каскад хміль",
        "Cascade hops",
        "cascade-hops",
        "hops",
        "7.49",
        30,
        "Класичний американський ароматний хміль з квітковими і грейпфрутовими нотами.",
        "Classic American aroma hop with floral and grapefruit notes.",
    ),
    (
        "Центенніал хміль",
        "Centennial hops",
        "centennial-hops",
        "hops",
        "6.49",
        18,
        "Насичений квітково-цитрусовий хміль для елю та IPA.",
        "Bold floral-citrus hop for ales and IPA.",
    ),
    (
        "Мозаїк хміль",
        "Mosaic hops",
        "mosaic-hops",
        "hops",
        "8.99",
        12,
        "Складний профіль з нотами чорниці, манго та сосни.",
        "Complex profile with blueberry, mango and pine notes.",
    ),
    (
        "Заац хміль",
        "Saaz hops",
        "saaz-hops",
        "hops",
        "5.49",
        40,
        "Благородний чеський хміль з м'яким трав'яним ароматом.",
        "Noble Czech hop with a soft herbal aroma.",
    ),
    (
        "Карамельний солод",
        "Caramel malt",
        "caramel-malt",
        "malts",
        "3.99",
        50,
        "Карамельна солодкість і насичений бурштиновий колір.",
        "Caramel sweetness and a rich amber color.",
    ),
    (
        "Маріс Оттер солод",
        "Maris Otter malt",
        "maris-otter-malt",
        "malts",
        "4.79",
        35,
        "Британський базовий солод з виразним бісквітним смаком.",
        "British base malt with a distinctive biscuit flavor.",
    ),
    (
        "Пілснер солод",
        "Pilsner malt",
        "pilsner-malt",
        "malts",
        "3.49",
        60,
        "Світлий чистий базовий солод для лагерів.",
        "Pale clean base malt for lagers.",
    ),
    (
        "Imperial дріжджі",
        "Imperial yeast",
        "imperial-yeast",
        "yeast",
        "12.99",
        15,
        "Рідкі дріжджі з високою кількістю клітин для швидкого старту бродіння.",
        "Liquid yeast with a high cell count for a fast fermentation start.",
    ),
    (
        "Safale US-05 дріжджі",
        "Safale US-05 yeast",
        "safale-us05-yeast",
        "yeast",
        "4.99",
        45,
        "Надійний американський ельовий штам з чистим профілем.",
        "Reliable American ale strain with a clean profile.",
    ),
    (
        "Несоложена пшениця",
        "Unmalted wheat",
        "unmalted-wheat",
        "adjuncts",
        "2.99",
        55,
        "Сира пшениця для witbier і lambic; додає тіло та легку каламутність.",
        "Raw wheat for witbier and lambic; adds body and a light haze.",
    ),
    (
        "Набір West Coast IPA",
        "West Coast IPA kit",
        "west-coast-ipa-kit",
        "kits",
        "49.99",
        8,
        "Усе необхідне для 20 літрів гіркого смолистого West Coast IPA.",
        "Everything you need for 20 liters of bitter resinous West Coast IPA.",
    ),
]

DEMO_ORDERS = [
    ("demo1@hopandbarley.example", ["citra-hops", "safale-us05-yeast"]),
    ("demo2@hopandbarley.example", ["cascade-hops", "caramel-malt"]),
    ("demo3@hopandbarley.example", ["maris-otter-malt", "west-coast-ipa-kit"]),
]

REVIEWS = [
    (
        "citra-hops",
        "demo1@hopandbarley.example",
        5,
        "Дуже насичений тропічний аромат.",
        "Very rich tropical aroma.",
    ),
    (
        "cascade-hops",
        "demo2@hopandbarley.example",
        5,
        "Грейпфрутові ноти саме те, що треба.",
        "Grapefruit notes are exactly what I needed.",
    ),
]


class Command(BaseCommand):
    """Seed the catalog with demo data and repair partially seeded databases."""

    help = "Create demo categories, products, users, orders, order items and reviews."

    def handle(self, *args: Any, **options: Any) -> None:
        categories = self._seed_categories()
        self._seed_products(categories)
        users = self._seed_users()
        self._seed_orders(users)
        self._seed_reviews(users)
        self.stdout.write(self.style.SUCCESS("Demo data ready."))

    def _seed_categories(self) -> dict[str, Category]:
        categories = {}
        for slug, name, name_en in CATEGORIES:
            category, _ = Category.objects.update_or_create(
                slug=slug,
                defaults={"name": name, "name_en": name_en},
            )
            categories[slug] = category
        return categories

    def _seed_products(self, categories: dict[str, Category]) -> None:
        for name, name_en, slug, category_slug, price, stock, description, description_en in (
            PRODUCTS
        ):
            Product.objects.update_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "name_en": name_en,
                    "category": categories[category_slug],
                    "price": Decimal(price),
                    "stock": stock,
                    "description": description,
                    "description_en": description_en,
                    "is_active": True,
                },
            )

    def _seed_users(self) -> dict[str, Any]:
        user_model = get_user_model()
        users = {}
        for i in range(1, 4):
            email = f"demo{i}@hopandbarley.example"
            user, created = user_model.objects.get_or_create(
                email=email,
                defaults={"first_name": f"Демо {i}", "last_name": "Пивовар"},
            )
            user.first_name = f"Демо {i}"
            user.last_name = "Пивовар"
            if created:
                user.set_password("demo-pass-123")
                user.save(update_fields=["first_name", "last_name", "password"])
            else:
                user.save(update_fields=["first_name", "last_name"])
            users[email] = user

        admin_email = "admin@hopandbarley.example"
        if not user_model.objects.filter(email=admin_email).exists():
            user_model.objects.create_superuser(email=admin_email, password="admin")
        return users

    def _seed_orders(self, users: dict[str, Any]) -> None:
        for email, slugs in DEMO_ORDERS:
            user = users[email]
            order = (
                Order.objects.filter(user=user, status=Order.Status.DELIVERED)
                .order_by("pk")
                .first()
            )
            if order is None:
                order = Order.objects.create(
                    user=user,
                    status=Order.Status.DELIVERED,
                    full_name=user.get_full_name(),
                    phone="+380501112233",
                    city="Київ",
                    address="Хрещатик 1",
                )
            self._sync_order_items(order, slugs)

    def _sync_order_items(self, order: Order, slugs: list[str]) -> None:
        total = Decimal("0")
        for slug in slugs:
            product = Product.objects.get(slug=slug)
            item, _ = OrderItem.objects.update_or_create(
                order=order,
                product=product,
                defaults={"quantity": 1, "price": product.price},
            )
            total += item.total_price
        order.total_price = total
        order.save(update_fields=["total_price"])

    def _seed_reviews(self, users: dict[str, Any]) -> None:
        keep_ids: list[int] = []
        for slug, email, rating, comment, comment_en in REVIEWS:
            review, _ = Review.objects.update_or_create(
                product=Product.objects.get(slug=slug),
                user=users[email],
                defaults={"rating": rating, "comment": comment, "comment_en": comment_en},
            )
            keep_ids.append(review.pk)
        Review.objects.filter(user__email__in=users.keys()).exclude(pk__in=keep_ids).delete()
