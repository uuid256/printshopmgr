from django.urls import path

from . import views

app_name = "documents"

urlpatterns = [
    path("", views.document_list, name="list"),
    path("<int:pk>/", views.document_detail, name="detail"),
    path("<int:pk>/pdf/", views.document_pdf, name="pdf"),
    path("job/<int:job_id>/quotation/", views.create_quotation, name="create_quotation"),
]
