"""Catalog views: product list, product detail with purchase-gated reviews."""

from decimal import Decimal, InvalidOperation
from typing import Any

from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.db import IntegrityError, transaction
from django.db.models import Avg, Count, F, Q, QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.views.generic import DetailView, ListView
from django.views.generic.edit import FormMixin

from config.context_processors import site_ui
from orders.cart import Cart

from .forms import ReviewForm
from .models import Category, Product
from .services import user_has_purchased

#: Maps the `sort` GET parameter to an ORM ordering.
SORTS = {
    "new": "-created_at",
    "price_asc": "price",
    "price_desc": "-price",
}


class ProductListView(ListView):
    """Home page and `/products/`: the filterable product catalog."""

    template_name = "products/product_list.html"
    context_object_name = "products"
    paginate_by = 8

    def get_queryset(self) -> QuerySet[Product]:
        qs: Any = (
            Product.objects.filter(is_active=True)
            .select_related("category")
            .annotate(avg_rating=Avg("reviews__rating"), sold=Count("order_items"))
        )
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(name__icontains=q)
                | Q(name_en__icontains=q)
                | Q(description__icontains=q)
                | Q(description_en__icontains=q)
            )

        categories = self.request.GET.getlist("category")
        if categories:
            qs = qs.filter(category__slug__in=categories)

        qs = self._filter_price(qs)

        sort = self.request.GET.get("sort", "new")
        if sort == "rating":
            return qs.order_by(F("avg_rating").desc(nulls_last=True))
        if sort == "popular":
            return qs.order_by("-sold", "-created_at")
        return qs.order_by(SORTS.get(sort, "-created_at"))

    def _filter_price(self, qs: QuerySet[Product]) -> QuerySet[Product]:
        """Apply price_min / price_max bounds, ignoring malformed input."""
        for param, lookup in (("price_min", "price__gte"), ("price_max", "price__lte")):
            raw = self.request.GET.get(param, "").strip()
            if not raw:
                continue
            try:
                qs = qs.filter(**{lookup: Decimal(raw)})
            except InvalidOperation:
                continue
        return qs

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.all()
        context["selected_categories"] = self.request.GET.getlist("category")
        context["current_sort"] = self.request.GET.get("sort", "new")
        return context


class ProductDetailView(FormMixin, DetailView):
    """Product page: details, reviews and the add-review form (POST)."""

    template_name = "products/product_detail.html"
    context_object_name = "product"
    form_class = ReviewForm

    def get_queryset(self) -> QuerySet[Product]:
        return Product.objects.filter(is_active=True).select_related("category")

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        product: Product = self.object
        user = self.request.user
        context["reviews"] = product.reviews.select_related("user")
        has_purchased = user_has_purchased(user, product)
        already_reviewed = (
            user.is_authenticated
            and product.reviews.filter(user=user).exists()
        )
        if not user.is_authenticated:
            review_state = "guest"
        elif not has_purchased:
            review_state = "not_purchased"
        elif already_reviewed:
            review_state = "already_reviewed"
        else:
            review_state = "can_review"
        context["review_state"] = review_state
        context["can_review"] = review_state == "can_review"
        context["in_cart"] = Cart(self.request).quantity_of(product)
        return context

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """Create a review; only buyers may post, one review per user."""
        self.object = self.get_object()
        ui = site_ui(request)["ui"]
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if not user_has_purchased(request.user, self.object):
            messages.error(request, ui["review_purchase_required"])
            return redirect(self.object.get_absolute_url())
        form = self.get_form()
        if form.is_valid():
            review = form.save(commit=False)
            review.product = self.object
            review.user = request.user
            try:
                with transaction.atomic():
                    review.save()
                messages.success(request, ui["review_thanks"])
            except IntegrityError:
                messages.error(request, ui["review_duplicate"])
            return redirect(self.object.get_absolute_url())
        return self.render_to_response(self.get_context_data(form=form))
