"""Template helpers for localized catalog text and product media."""

from django import template
from django.templatetags.static import static

register = template.Library()

_PRODUCT_IMAGE_MAP = {
    "citra-hops": "img/products/citra_hops.jpg",
    "cascade-hops": "img/products/cascade_hops.jpg",
    "centennial-hops": "img/products/centennial_hops.jpg",
    "mosaic-hops": "img/products/mosaic_hops.jpg",
    "saaz-hops": "img/products/saaz_hops.jpg",
    "caramel-malt": "img/products/caramel_malt.jpg",
    "maris-otter-malt": "img/products/maris_otter_malt.jpg",
    "pilsner-malt": "img/products/pilsner_malt.jpg",
    "imperial-yeast": "img/products/imperial_yeast.jpg",
    "safale-us05-yeast": "img/products/safale_us05_yeast.jpg",
    "unmalted-wheat": "img/products/unmalted_wheat.jpg",
    "west-coast-ipa-kit": "img/products/ipa_kit.jpg",
}


@register.filter
def product_image_url(product) -> str:
    """Return the uploaded image or a static fallback for seeded products."""
    image = getattr(product, "image", None)
    if image:
        try:
            return image.url
        except ValueError:
            pass
    slug = getattr(product, "slug", "")
    return static(_PRODUCT_IMAGE_MAP.get(slug, "img/background/pattern.jpg"))


@register.filter
def localized_name(obj, language: str = "uk") -> str:
    """Return a localized name for a category or product."""
    method = getattr(obj, "localized_name", None)
    if callable(method):
        return method(language)
    return getattr(obj, "name", "")


@register.filter
def localized_description(obj, language: str = "uk") -> str:
    """Return a localized product description."""
    method = getattr(obj, "localized_description", None)
    if callable(method):
        return method(language)
    return getattr(obj, "description", "")


@register.filter
def localized_comment(obj, language: str = "uk") -> str:
    """Return a localized review comment."""
    method = getattr(obj, "localized_comment", None)
    if callable(method):
        return method(language)
    return getattr(obj, "comment", "")
