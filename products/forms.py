"""Catalog forms."""

from django import forms

from .models import Review


class ReviewForm(forms.ModelForm):
    """A star rating with a comment; styled with the design's form classes."""

    rating = forms.TypedChoiceField(
        coerce=int,
        choices=[(i, str(i)) for i in range(5, 0, -1)],
        widget=forms.RadioSelect(attrs={"class": "review-star-input"}),
        initial=5,
    )

    class Meta:
        model = Review
        fields = ["rating", "comment"]
        widgets = {
            "comment": forms.Textarea(attrs={"class": "Textarea", "rows": 3}),
        }
