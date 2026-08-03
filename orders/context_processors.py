"""Template context processors for order-related UI state."""

from .cart import Cart


def cart_summary(request):
    """Expose the current cart item count to all templates."""
    return {"cart_count": len(Cart(request))}
