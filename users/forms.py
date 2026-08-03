"""Account forms styled after the design (email + single password)."""

from typing import Any

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password

from .models import User


PLACEHOLDERS = {
    "uk": {
        "email": "Електронна пошта",
        "password": "Пароль",
        "full_name": "Повне ім'я",
        "phone": "Номер телефону",
        "city": "Місто",
        "address": "Адреса доставки",
    },
    "en": {
        "email": "Email address",
        "password": "Password",
        "full_name": "Full name",
        "phone": "Phone number",
        "city": "City",
        "address": "Shipping address",
    },
}


class LoginForm(AuthenticationForm):
    """Email/password login with the design's input classes."""

    def set_language(self, language: str) -> None:
        """Localize placeholders for the current UI language."""
        placeholders = PLACEHOLDERS.get(language, PLACEHOLDERS["uk"])
        self.fields["username"].widget.attrs.update(
            {"class": "Input", "placeholder": placeholders["email"]}
        )
        self.fields["password"].widget.attrs.update(
            {"class": "Input", "placeholder": placeholders["password"]}
        )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.set_language("uk")


class RegisterForm(forms.ModelForm):
    """Registration exactly as designed: email, password, remember me."""

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "Input", "placeholder": "Password"})
    )
    remember_me = forms.BooleanField(required=False, initial=True)

    def set_language(self, language: str) -> None:
        """Localize placeholders for the current UI language."""
        placeholders = PLACEHOLDERS.get(language, PLACEHOLDERS["uk"])
        self.fields["email"].widget.attrs["placeholder"] = placeholders["email"]
        self.fields["password"].widget.attrs["placeholder"] = placeholders["password"]

    class Meta:
        model = User
        fields = ["email"]
        widgets = {
            "email": forms.EmailInput(
                attrs={"class": "Input", "placeholder": PLACEHOLDERS["uk"]["email"]}
            )
        }

    def clean_password(self) -> str:
        password: str = self.cleaned_data["password"]
        validate_password(password)
        return password

    def save(self, commit: bool = True) -> User:
        """Create the user with a properly hashed password."""
        return User.objects.create_user(
            email=self.cleaned_data["email"], password=self.cleaned_data["password"]
        )


class ProfileForm(forms.ModelForm):
    """Account page personal info; full_name maps to first/last name."""

    full_name = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(
            attrs={"class": "Input", "placeholder": PLACEHOLDERS["uk"]["full_name"]}
        ),
    )

    def set_language(self, language: str) -> None:
        """Localize placeholders for the current UI language."""
        placeholders = PLACEHOLDERS.get(language, PLACEHOLDERS["uk"])
        self.fields["full_name"].widget.attrs["placeholder"] = placeholders["full_name"]
        self.fields["email"].widget.attrs["placeholder"] = placeholders["email"]
        self.fields["phone"].widget.attrs["placeholder"] = placeholders["phone"]
        self.fields["city"].widget.attrs["placeholder"] = placeholders["city"]
        self.fields["address"].widget.attrs["placeholder"] = placeholders["address"]

    class Meta:
        model = User
        fields = ["email", "phone", "city", "address"]
        widgets = {
            "email": forms.EmailInput(
                attrs={"class": "Input", "placeholder": PLACEHOLDERS["uk"]["email"]}
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
        }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["full_name"].initial = self.instance.get_full_name()
            self.fields["email"].initial = self.instance.email
            self.fields["phone"].initial = self.instance.phone
            self.fields["city"].initial = self.instance.city
            self.fields["address"].initial = self.instance.address

    def save(self, commit: bool = True) -> User:
        """Split full_name into first/last before saving."""
        user: User = super().save(commit=False)
        full_name = self.cleaned_data.get("full_name", "").split()
        if full_name:
            user.first_name = full_name[0]
            user.last_name = " ".join(full_name[1:])
        else:
            user.first_name = ""
            user.last_name = ""
        if commit:
            user.save()
        return user
