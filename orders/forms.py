"""Checkout form styled with the design's classes."""

from django import forms

from .models import Order


PLACEHOLDERS = {
    "uk": {
        "full_name": "Повне ім'я",
        "phone": "Номер телефону",
        "city": "Місто",
        "address": "Вулиця, будинок, квартира",
    },
    "en": {
        "full_name": "Full name",
        "phone": "Phone number",
        "city": "City",
        "address": "Street address",
    },
}


class CheckoutForm(forms.ModelForm):
    """Shipping details + payment method for the order."""

    def set_language(self, language: str) -> None:
        """Localize placeholders for the current UI language."""
        placeholders = PLACEHOLDERS.get(language, PLACEHOLDERS["uk"])
        self.fields["full_name"].widget.attrs["placeholder"] = placeholders["full_name"]
        self.fields["phone"].widget.attrs["placeholder"] = placeholders["phone"]
        self.fields["city"].widget.attrs["placeholder"] = placeholders["city"]
        self.fields["address"].widget.attrs["placeholder"] = placeholders["address"]

    class Meta:
        model = Order
        fields = ["full_name", "phone", "city", "address", "payment_method"]
        widgets = {
            "full_name": forms.TextInput(
                attrs={"class": "Input", "placeholder": PLACEHOLDERS["uk"]["full_name"]}
            ),
            "phone": forms.TextInput(
                attrs={"class": "Input", "placeholder": PLACEHOLDERS["uk"]["phone"]}
            ),
            "city": forms.TextInput(
                attrs={"class": "Input", "placeholder": PLACEHOLDERS["uk"]["city"]}
            ),
            "address": forms.Textarea(
                attrs={
                    "class": "Textarea",
                    "rows": 3,
                    "placeholder": PLACEHOLDERS["uk"]["address"],
                }
            ),
            "payment_method": forms.RadioSelect(),
        }
