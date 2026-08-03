import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_guides_page_renders_with_base_layout(client) -> None:
    response = client.get(reverse("guides"))
    assert response.status_code == 200
    content = response.content.decode()
    assert "Hop & Barley" in content
    assert "Посібники та рецепти" in content
    assert "Увійти" in content
    assert reverse("orders:cart") in content


@pytest.mark.parametrize(
    "route, heading",
    [
        ("community", "Спільнота"),
        ("resources", "Ресурси"),
        ("contact", "Контакт"),
        ("faq", "FAQ"),
        ("license", "Ліцензія"),
    ],
)
@pytest.mark.django_db
def test_static_pages_render(client, route: str, heading: str) -> None:
    response = client.get(reverse(route))
    assert response.status_code == 200
    assert heading in response.content.decode()


@pytest.mark.django_db
def test_language_switch_persists_in_session(client) -> None:
    response = client.post(reverse("set_language", args=["en"]), {"next": reverse("guides")})
    assert response.status_code == 302
    html = client.get(reverse("guides")).content.decode()
    assert 'lang="en"' in html
    assert "Sign in" in html
