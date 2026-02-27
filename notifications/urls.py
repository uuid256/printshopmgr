from django.urls import path

from . import views

app_name = "notifications"

urlpatterns = [
    path("line/webhook/", views.line_webhook, name="line_webhook"),
]
