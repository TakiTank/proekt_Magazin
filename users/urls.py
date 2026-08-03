from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from . import views

app_name = "users"

urlpatterns = [
    path("account/", views.account, name="account"),
    path("account/register/", views.register, name="register"),
    path("account/login/", views.UserLoginView.as_view(), name="login"),
    path("account/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path(
        "account/password/",
        views.UserPasswordChangeView.as_view(),
        name="password_change",
    ),
    path(
        "account/password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="users/password_reset.html",
            email_template_name="users/password_reset_email.txt",
            success_url=reverse_lazy("users:password_reset_done"),
        ),
        name="password_reset",
    ),
    path(
        "account/password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="users/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "account/password-reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="users/password_reset_confirm.html",
            success_url=reverse_lazy("users:password_reset_complete"),
        ),
        name="password_reset_confirm",
    ),
    path(
        "account/password-reset/complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="users/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
]
