"""Account views: registration, login, account page, password change."""

from typing import Any, cast

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy

from orders.models import Order
from orders.cart import Cart
from config.context_processors import site_ui

from .forms import LoginForm, ProfileForm, RegisterForm
from .models import User


ACCOUNT_TABS = {"order-history", "account-info", "password", "cart"}


class UserLoginView(LoginView):
    """Session login with the design template."""

    template_name = "users/login.html"
    authentication_form = LoginForm

    def get_form(self, form_class: Any | None = None) -> LoginForm:
        form = cast(LoginForm, super().get_form(form_class))
        form.set_language(site_ui(self.request)["site_language"])
        return form


def _active_account_tab(request: HttpRequest, fallback: str = "order-history") -> str:
    tab = request.GET.get("tab", fallback)
    return tab if tab in ACCOUNT_TABS else fallback


def register(request: HttpRequest) -> HttpResponse:
    """Create an account and log the user in immediately."""
    site = site_ui(request)
    ui = site["ui"]
    form = RegisterForm(request.POST or None)
    form.set_language(site["site_language"])
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        if not form.cleaned_data["remember_me"]:
            request.session.set_expiry(0)  # browser-session cookie
        messages.success(request, ui["welcome_message"])
        return redirect("home")
    return render(request, "users/register.html", {"form": form})


@login_required
def account(request: HttpRequest) -> HttpResponse:
    """Account page: order history with status filter, profile editing."""
    user = cast(User, request.user)  # guaranteed by @login_required
    site = site_ui(request)
    ui = site["ui"]
    active_tab = _active_account_tab(request)
    form = ProfileForm(request.POST or None, instance=user)
    form.set_language(site["site_language"])
    cart = Cart(request)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, ui["profile_updated"])
        return redirect(f"{reverse('users:account')}?tab=account-info")
    if request.method == "POST":
        active_tab = "account-info"

    orders = Order.objects.filter(user=user).prefetch_related("items")
    status = request.GET.get("status", "")
    if status in Order.Status.values:
        orders = orders.filter(status=status)
    page = Paginator(orders, 5).get_page(request.GET.get("page"))

    return render(
        request,
        "users/account.html",
        {
            "form": form,
            "orders_page": page,
            "current_status": status,
            "statuses": Order.Status.choices,
            "password_form": PasswordChangeForm(user=request.user),
            "active_tab": active_tab,
            "cart": cart,
        },
    )


class UserPasswordChangeView(PasswordChangeView):
    """POST-only password change from the account page tab."""

    success_url = reverse_lazy("users:account")
    template_name = "users/account.html"

    def get_success_url(self) -> str:
        return f"{reverse('users:account')}?tab=password"

    def form_valid(self, form: Any) -> HttpResponse:
        messages.success(self.request, site_ui(self.request)["ui"]["password_changed"])
        return super().form_valid(form)

    def form_invalid(self, form: Any) -> HttpResponse:
        for error in form.errors.values():
            messages.error(self.request, error.as_text())
        return redirect(f"{reverse('users:account')}?tab=password")
