# Hop & Barley

Hop & Barley - навчальний Django/DRF інтернет-магазин товарів для пивоваріння.
Проєкт містить каталог, кошик у сесії, checkout, особистий кабінет, адмінку,
REST API з JWT та Swagger/OpenAPI документацію.

## Можливості

- Каталог товарів: пошук, фільтри, сортування, пагінація.
- Детальна сторінка товару з відгуками після покупки.
- Кошик `/cart/`: додавання, видалення, зміна кількості, перевірка залишків.
- Checkout `/checkout/`: адреса доставки, mock-оплата, створення замовлення, email.
- Account `/account/`: реєстрація, вхід/вихід, історія замовлень, профіль, пароль.
- Admin `/admin/`: товари, категорії, замовлення, відгуки, користувачі, аналітика.
- REST API `/api/`: товари, кошик, замовлення, користувачі, відгуки.
- GraphQL `/graphql/`: каталог + аналітика (GraphiQL).
- Swagger UI: `/api/docs/`, OpenAPI schema: `/api/schema/`.
- Перемикач мови інтерфейсу: українська / англійська (UI + каталог).

## Вимоги

- Python 3.13+
- PostgreSQL 16+ або Docker Compose
- `requirements.txt` містить усі Python-залежності

Основні залежності: Django, Django REST Framework, SimpleJWT, drf-spectacular,
psycopg, Pillow, Whitenoise, Gunicorn, pytest-django, flake8, mypy.

## Швидкий запуск через Docker

```powershell
docker compose up --build
```

Docker Compose піднімає два сервіси:

- `db` - PostgreSQL.
- `web` - Django application, migrations, demo seed, collectstatic, gunicorn.

Після запуску:

- сайт: `http://localhost:8000/`
- адмінка: `http://localhost:8000/admin/`
- Swagger: `http://localhost:8000/api/docs/`

## Локальний запуск

1. Створити і активувати virtualenv:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Встановити залежності:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

3. Налаштувати `.env` за прикладом `.env.example` або передати змінні середовища.
За замовчуванням проєкт очікує PostgreSQL:

```powershell
$env:POSTGRES_DB="shop"
$env:POSTGRES_USER="shop"
$env:POSTGRES_PASSWORD="shop"
$env:POSTGRES_HOST="localhost"
$env:POSTGRES_PORT="5432"
```

Для швидкого локального запуску без PostgreSQL можна тимчасово використати SQLite:

```powershell
$env:DB_ENGINE="sqlite"
```

4. Застосувати міграції, додати demo-дані і запустити сервер:

```powershell
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_demo
.\.venv\Scripts\python.exe manage.py runserver
```

## Тести, лінтери, типізація

Проєкт використовує `pytest-django`, `flake8` і `mypy`.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m flake8
.\.venv\Scripts\python.exe -m mypy .
.\.venv\Scripts\python.exe manage.py check
```

Тести покривають основні сценарії:

- каталог, фільтри, пошук, пагінація;
- кошик, session storage, ліміти залишків;
- checkout, транзакції, emails;
- реєстрація, login/logout, account, зміна пароля;
- REST API, JWT, доступ лише до своїх замовлень;
- бізнес-логіка кошика і замовлень;
- адмін-аналітика та admin actions.

## REST API

Документація доступна за адресами:

- Swagger UI: `GET /api/docs/`
- OpenAPI schema: `GET /api/schema/`

### JWT

Login:

```http
POST /api/users/login/
Content-Type: application/json
```

```json
{
  "email": "demo@example.com",
  "password": "strong-pass-123"
}
```

Відповідь містить два токени:

```json
{
  "refresh": "<refresh-token>",
  "access": "<access-token>"
}
```

`access` використовується для авторизованих запитів:

```http
Authorization: Bearer <access-token>
```

Оновлення access-токена:

```http
POST /api/users/refresh/
Content-Type: application/json
```

```json
{
  "refresh": "<refresh-token>"
}
```

У налаштуваннях:

- access token живе 30 хвилин;
- refresh token живе 7 днів;
- тип заголовка: `Bearer`.

### Приклади API-запитів

Список товарів:

```http
GET /api/products/?q=hops&page=1
```

Деталі товару:

```http
GET /api/products/citra-hops/
```

Додати товар у кошик:

```http
POST /api/cart/
Content-Type: application/json
```

```json
{
  "product_id": 1,
  "quantity": 2
}
```

Змінити кількість:

```http
PATCH /api/cart/
Content-Type: application/json
```

```json
{
  "product_id": 1,
  "quantity": 1
}
```

Створити замовлення з поточного кошика:

```http
POST /api/orders/
Authorization: Bearer <access-token>
Content-Type: application/json
```

```json
{
  "full_name": "Ivan Brewer",
  "phone": "+380501112233",
  "city": "Kyiv",
  "address": "Khreshchatyk 1",
  "payment_method": "debit"
}
```

Список своїх замовлень:

```http
GET /api/orders/
Authorization: Bearer <access-token>
```

Скасувати своє замовлення:

```http
PATCH /api/orders/1/
Authorization: Bearer <access-token>
Content-Type: application/json
```

```json
{
  "status": "cancelled"
}
```

Додати відгук до купленого товару:

```http
POST /api/products/citra-hops/reviews/
Authorization: Bearer <access-token>
Content-Type: application/json
```

```json
{
  "rating": 5,
  "comment": "Good product"
}
```

## Структура проєкту

- `config/` - settings, URL routing, site-level views, admin metrics.
- `products/` - каталог, товари, категорії, відгуки.
- `orders/` - session cart, checkout, order models, emails, services.
- `users/` - custom user model, auth, account page, profile forms.
- `api/` - DRF serializers, viewsets, JWT endpoints, Swagger routes.
- `templates/` - Django templates.
- `static/` - CSS, JS, images.
- `tests/` - pytest suite.
- `Dockerfile`, `docker-compose.yml` - локальна інфраструктура.

## Якість коду

- Публічні модулі та важлива бізнес-логіка мають docstrings.
- Основні функції та методи мають type hints.
- `flake8` налаштований у `setup.cfg`.
- `mypy` та `pytest-django` налаштовані у `pyproject.toml`.
- Основна БД для застосунку - PostgreSQL.
- SQLite використовується тільки у тестових налаштуваннях або для швидкого локального запуску.

## Git workflow

Рекомендована схема:

- `main` - стабільна гілка.
- `develop/...` - інтеграційні зміни.
- `feature/...` - окремі задачі.

Коміти варто робити невеликими і змістовними, наприклад:

- `feature/cart-stock-validation`
- `feature/api-jwt-docs`
- `fix/account-profile-validation`

## Статус бонусів

GraphQL: `/graphql/` (GraphiQL). Приклади:

```graphql
{
  categories { slug name nameEn }
  products(category: "hops") { slug name nameEn price inStock }
  orderAnalytics { orderCount paidOrderCount revenue averageCheck }
  popularProducts(limit: 5) { slug name soldUnits stock }
  userActivity(limit: 5) { email orderCount totalSpent isRepeatBuyer }
}
```
