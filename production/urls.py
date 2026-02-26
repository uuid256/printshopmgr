from django.urls import path

from . import views

app_name = "production"

urlpatterns = [
    path("queue/", views.production_queue, name="queue"),
    path("queue/<int:job_id>/status/", views.update_job_status, name="update_status"),
]
