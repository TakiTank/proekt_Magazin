"""Catalog models: categories, products and customer reviews."""

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse


class Category(models.Model):
    """Product category; `parent` enables nested categories."""

    name = models.CharField(max_length=120)
    name_en = models.CharField(max_length=120, blank=True)
    slug = models.SlugField(max_length=140, unique=True)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE, related_name="children"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self) -> str:
        return self.name

    def localized_name(self, language: str = "uk") -> str:
        """Return the category name for the selected UI language."""
        if language == "en" and self.name_en:
            return self.name_en
        return self.name


class Product(models.Model):
    """A catalog item sold by the shop."""

    name = models.CharField(max_length=200)
    name_en = models.CharField(max_length=200, blank=True)
    slug = models.SlugField(max_length=220, unique=True)
    description = models.TextField()
    description_en = models.TextField(blank=True)
    price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    image = models.ImageField(upload_to="products/", blank=True)
    is_active = models.BooleanField(default=True)
    stock = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        """Canonical product page URL."""
        return reverse("products:detail", kwargs={"slug": self.slug})

    @property
    def in_stock(self) -> bool:
        """Whether at least one unit is available."""
        return self.stock > 0

    def localized_name(self, language: str = "uk") -> str:
        """Return the product name for the selected UI language."""
        if language == "en" and self.name_en:
            return self.name_en
        return self.name

    def localized_description(self, language: str = "uk") -> str:
        """Return the product description for the selected UI language."""
        if language == "en" and self.description_en:
            return self.description_en
        return self.description


class Review(models.Model):
    """A 1-5 star review left by a customer who bought the product."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews"
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField()
    comment_en = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["product", "user"], name="one_review_per_user")
        ]

    def __str__(self) -> str:
        return f"{self.product}: {self.rating}/5 by {self.user}"

    def localized_comment(self, language: str = "uk") -> str:
        """Return the review comment for the selected UI language."""
        if language == "en" and self.comment_en:
            return self.comment_en
        return self.comment
