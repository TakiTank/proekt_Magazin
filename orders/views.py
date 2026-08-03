"""Cart and checkout views."""

from typing import cast

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from products.models import Product
from users.models import User

from config.context_processors import site_ui

from .cart import Cart, CartQuantityError
from .emails import send_order_emails
from .forms import CheckoutForm
from .models import Order
from .services import InsufficientStock, create_order


def cart_detail(request: HttpRequest) -> HttpResponse:
    """Show the cart contents with server-computed totals."""
    return render(request, "orders/cart.html", {"cart": Cart(request)})


def _quantity(request: HttpRequest) -> int:
    """Parse the quantity field, defaulting to 1."""
    try:
        return max(1, int(request.POST.get("quantity", "1")))
    except ValueError:
        return 1


@require_POST
def cart_add(request: HttpRequest, product_id: int) -> HttpResponse:
    """Add N units of a product to the session cart."""
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    site = site_ui(request)
    ui = site["ui"]
    language = site["site_language"]
    product_label = product.localized_name(language)
    try:
        Cart(request).add(product, _quantity(request))
        messages.success(request, ui["cart_item_added"].format(product=product_label))
    except CartQuantityError as exc:
        messages.error(
            request,
            ui["cart_item_unavailable"].format(available=exc.available, product=product_label),
        )
    next_url = request.POST.get("next", "")
    if next_url and url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return redirect(next_url)
    return redirect("orders:cart")


@require_POST
def cart_update(request: HttpRequest, product_id: int) -> HttpResponse:
    """Set the exact quantity for a cart line."""
    product = get_object_or_404(Product, pk=product_id)
    site = site_ui(request)
    ui = site["ui"]
    try:
        Cart(request).set_quantity(product, _quantity(request))
    except CartQuantityError as exc:
        messages.error(
            request,
            ui["cart_item_unavailable"].format(
                available=exc.available,
                product=product.localized_name(site["site_language"]),
            ),
        )
    return redirect("orders:cart")


@require_POST
def cart_remove(request: HttpRequest, product_id: int) -> HttpResponse:
    """Remove a product line from the cart."""
    product = get_object_or_404(Product, pk=product_id)
    Cart(request).remove(product)
    return redirect("orders:cart")


@login_required
def checkout(request: HttpRequest) -> HttpResponse:
    """Checkout page: validate the form, create the order, send emails."""
    cart = Cart(request)
    site = site_ui(request)
    ui = site["ui"]
    if len(cart) == 0:
        messages.error(request, ui["cart_empty_message"])
        return redirect("orders:cart")

    user = cast(User, request.user)  # guaranteed by @login_required
    form = CheckoutForm(
        request.POST or None,
        initial={
            "full_name": user.get_full_name(), "phone": user.phone,
            "city": user.city, "address": user.address,
        },
    )
    form.set_language(site["site_language"])
    if request.method == "POST" and form.is_valid():
        try:
            order = create_order(user, cart, **form.cleaned_data)
        except InsufficientStock as exc:
            messages.error(
                request,
                ui["cart_item_unavailable"].format(
                    available=exc.available,
                    product=exc.product.localized_name(site["site_language"]),
                ),
            )
        else:
            cart.clear()
            send_order_emails(order)
            return redirect("orders:success", pk=order.pk)
    return render(request, "orders/checkout.html", {"form": form, "cart": cart})


@login_required
def order_success(request: HttpRequest, pk: int) -> HttpResponse:
    """Thank-you page after a successful checkout."""
    order = get_object_or_404(Order, pk=pk, user=request.user)
    return render(request, "orders/order_success.html", {"order": order})


@login_required
def order_detail(request: HttpRequest, pk: int) -> HttpResponse:
    """Show one order with line items for the current user only."""
    order = get_object_or_404(
        Order.objects.prefetch_related("items__product"),
        pk=pk,
        user=request.user,
    )
    return render(request, "orders/order_detail.html", {"order": order})


@login_required
@require_POST
def order_reorder(request: HttpRequest, pk: int) -> HttpResponse:
    """Add all products from a past order back into the session cart."""
    order = get_object_or_404(
        Order.objects.prefetch_related("items__product"),
        pk=pk,
        user=request.user,
    )
    cart = Cart(request)
    site = site_ui(request)
    ui = site["ui"]
    language = site["site_language"]
    added = 0
    for item in order.items.all():
        product = item.product
        if not product.is_active or product.stock <= 0:
            continue
        try:
            cart.add(product, min(item.quantity, product.stock))
            added += 1
        except CartQuantityError as exc:
            messages.error(
                request,
                ui["cart_item_unavailable"].format(
                    available=exc.available,
                    product=product.localized_name(language),
                ),
            )
    if added:
        messages.success(request, ui["reorder_added"])
    return redirect("orders:cart")
