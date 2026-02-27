from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="accounts/login.html"),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    # LINE Login OAuth — staff connect their personal LINE account
    path("line-login/", views.line_login_redirect, name="line_login"),
    path("line-callback/", views.line_login_callback, name="line_callback"),
    path("line-disconnect/", views.line_disconnect, name="line_disconnect"),
]
