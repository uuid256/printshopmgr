from django.urls import path

from . import views

app_name = "public"

urlpatterns = [
    path("<uuid:token>/", views.job_tracking, name="track"),
]
