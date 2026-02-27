from django.urls import path

from . import views

app_name = "public"

urlpatterns = [
    path("<uuid:token>/", views.job_tracking, name="track"),
    path("<uuid:token>/approve/", views.job_approve, name="approve"),
    path("<uuid:token>/revision/", views.job_request_revision, name="revision"),
]
