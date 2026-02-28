from django.urls import path

from . import views

app_name = "documents"

urlpatterns = [
    path("", views.document_list, name="list"),
    path("<int:pk>/", views.document_detail, name="detail"),
    path("<int:pk>/pdf/", views.document_pdf, name="pdf"),
    path("<int:pk>/void/", views.void_document, name="void"),
    path("job/<int:job_id>/quotation/", views.create_quotation, name="create_quotation"),
    path("job/<int:job_id>/tax-invoice/", views.create_tax_invoice, name="create_tax_invoice"),
    path("aging/", views.aging_report, name="aging"),
    path("aging/export/", views.aging_export_excel, name="aging_export"),
    path("vat-report/", views.vat_report, name="vat_report"),
    path("vat-report/export/", views.vat_report_export_excel, name="vat_report_export"),
    path("revenue/", views.revenue_report, name="revenue"),
    path("statement/<int:customer_id>/", views.monthly_statement, name="monthly_statement"),
]
