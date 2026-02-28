from django.urls import path

from . import views

app_name = "jobs"

urlpatterns = [
    path("", views.job_list, name="list"),
    path("kanban/", views.design_kanban, name="kanban"),
    path("new/", views.job_create, name="create"),
    path("<int:pk>/", views.job_detail, name="detail"),
    path("<int:pk>/edit/", views.job_edit, name="edit"),
    path("<int:pk>/reorder/", views.job_reorder, name="reorder"),
    path("<int:pk>/slip/", views.job_slip_pdf, name="slip"),
    path("<int:pk>/status/", views.job_update_status, name="update_status"),
    path("<int:pk>/files/upload/", views.job_file_upload, name="file_upload"),
    path("<int:pk>/files/<int:file_pk>/delete/", views.job_file_delete, name="file_delete"),
    # HTMX: inline price calculation
    path("calculate-price/", views.calculate_price, name="calculate_price"),
]
