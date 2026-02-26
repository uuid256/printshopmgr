from django.urls import path

from . import views

app_name = "payments"

urlpatterns = [
    path("job/<int:job_id>/pay/", views.payment_screen, name="pay"),
    path("job/<int:job_id>/receipt/", views.payment_receipt, name="receipt"),
    # HTMX: generate PromptPay QR code
    path("promptpay-qr/", views.generate_promptpay_qr, name="promptpay_qr"),
]
