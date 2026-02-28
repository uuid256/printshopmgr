from django.urls import path

from . import views

app_name = "notifications"

urlpatterns = [
    path("line/webhook/", views.line_webhook, name="line_webhook"),
    path("settings/", views.notification_settings, name="settings"),
    path("test-email/", views.send_test_email, name="test_email"),
    path("", views.notification_list, name="list"),
    path("mark-read/", views.notification_mark_read, name="mark_read"),
]
