from django.urls import path

from . import views

app_name = "jobs"

urlpatterns = [
    path("", views.job_list, name="list"),
    path("new/", views.job_create, name="create"),
    path("<int:pk>/", views.job_detail, name="detail"),
    path("<int:pk>/edit/", views.job_edit, name="edit"),
    path("<int:pk>/status/", views.job_update_status, name="update_status"),
    # HTMX: inline price calculation
    path("calculate-price/", views.calculate_price, name="calculate_price"),
]
