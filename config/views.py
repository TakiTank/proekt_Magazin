"""Small utility views for site-level settings."""

from __future__ import annotations

from typing import Any

from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme


STATIC_PAGES: dict[str, dict[str, dict[str, Any]]] = {
    "guides": {
        "uk": {
            "page_title": "Посібники та рецепти",
            "page_heading": "Посібники та рецепти",
            "page_intro": "Тут зібрані практичні поради та рецепти для пивоваріння.",
            "page_points": [
                "Як підбирати хміль і солод.",
                "Базові рецепти для домашнього варіння.",
                "Поради щодо температури, ферментації та витримки.",
            ],
        },
        "en": {
            "page_title": "Guides & Recipes",
            "page_heading": "Guides & Recipes",
            "page_intro": "Practical brewing guides and recipes are collected here.",
            "page_points": [
                "How to choose hops and malt.",
                "Starter recipes for home brewing.",
                "Tips on temperature, fermentation and conditioning.",
            ],
        },
    },
    "community": {
        "uk": {
            "page_title": "Спільнота",
            "page_heading": "Спільнота",
            "page_intro": (
                "Приєднуйтесь до спільноти Hop & Barley, щоб ділитися рецептами, "
                "порадами та досвідом."
            ),
            "page_points": [
                "Обговорення рецептів",
                "Поради з варіння",
                "Обмін досвідом між учасниками",
            ],
        },
        "en": {
            "page_title": "Community",
            "page_heading": "Community",
            "page_intro": "Join the Hop & Barley community to share recipes, tips and experience.",
            "page_points": ["Recipe discussions", "Brew-day tips", "Community knowledge sharing"],
        },
    },
    "resources": {
        "uk": {
            "page_title": "Ресурси",
            "page_heading": "Ресурси",
            "page_intro": "Практичні матеріали для вибору інгредієнтів, обладнання та рецептів.",
            "page_points": ["Інгредієнти", "Обладнання", "Інструкції та калькулятори"],
        },
        "en": {
            "page_title": "Resources",
            "page_heading": "Resources",
            "page_intro": "Practical materials for ingredients, equipment and recipes.",
            "page_points": ["Ingredients", "Equipment", "Guides and calculators"],
        },
    },
    "contact": {
        "uk": {
            "page_title": "Контакт",
            "page_heading": "Контакт",
            "page_intro": (
                "Напишіть нам, якщо потрібна допомога з замовленням, товаром "
                "або акаунтом."
            ),
            "page_points": [
                "support@hopandbarley.example",
                "+380 44 000 00 00",
                "Пн-Пт, 09:00-18:00",
            ],
        },
        "en": {
            "page_title": "Contact",
            "page_heading": "Contact",
            "page_intro": "Contact us if you need help with your order, products or account.",
            "page_points": [
                "support@hopandbarley.example",
                "+380 44 000 00 00",
                "Mon-Fri, 09:00-18:00",
            ],
        },
    },
    "faq": {
        "uk": {
            "page_title": "FAQ",
            "page_heading": "FAQ",
            "page_intro": (
                "Відповіді на найпоширеніші питання про замовлення, доставку "
                "та акаунт."
            ),
            "page_points": [
                "Замовлення оформлюються через кошик.",
                "Оплата підтримує кілька способів.",
                "Профіль можна редагувати в акаунті.",
            ],
        },
        "en": {
            "page_title": "FAQ",
            "page_heading": "FAQ",
            "page_intro": (
                "Answers to the most common questions about ordering, shipping "
                "and accounts."
            ),
            "page_points": [
                "Orders are placed through the cart.",
                "Multiple payment methods are available.",
                "Profiles can be edited in the account page.",
            ],
        },
    },
    "license": {
        "uk": {
            "page_title": "Ліцензія",
            "page_heading": "Ліцензія",
            "page_intro": (
                "Матеріали проєкту та зображення використовуються для "
                "демо-вітрини Hop & Barley."
            ),
            "page_points": [
                "Демо-матеріали",
                "Код і шаблони проєкту",
                "Звертайтесь за дозволом на повторне використання",
            ],
        },
        "en": {
            "page_title": "License",
            "page_heading": "License",
            "page_intro": (
                "Project materials and images are used for the Hop & Barley "
                "demo storefront."
            ),
            "page_points": [
                "Demo materials",
                "Project code and templates",
                "Contact us for reuse permissions",
            ],
        },
    },
}


def localized_static_page(page_key: str):
    """Render a small informational page in the selected UI language."""

    def view(request: HttpRequest) -> HttpResponse:
        language = request.session.get("site_language", "uk")
        data = STATIC_PAGES[page_key].get(language, STATIC_PAGES[page_key]["uk"])
        return render(request, "pages/static_page.html", data)

    return view


def set_language(request: HttpRequest, code: str) -> HttpResponse:
    """Persist the selected UI language in the session."""
    if code not in {"en", "uk"}:
        code = "uk"
    request.session["site_language"] = code
    next_url = request.POST.get("next") or request.GET.get("next") or "/"
    if not url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        next_url = "/"
    return redirect(next_url)
