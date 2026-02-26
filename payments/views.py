"""Payment views — collection screen and PromptPay QR generation."""

import base64
import io

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from accounts.mixins import role_required
from accounts.models import Role
from jobs.models import Job

from .models import BankAccount, Payment, PaymentMethod


@role_required(Role.COUNTER, Role.OWNER)
def payment_screen(request, job_id):
    """Main payment collection screen."""
    job = get_object_or_404(Job.objects.select_related("customer"), pk=job_id)
    bank_accounts = BankAccount.objects.filter(is_active=True)
    existing_payments = job.payments.select_related("received_by").order_by("-received_at")

    if request.method == "POST":
        amount = request.POST.get("amount")
        method = request.POST.get("method")
        bank_account_id = request.POST.get("bank_account") or None
        reference = request.POST.get("reference_number", "")
        is_deposit = request.POST.get("is_deposit") == "true"

        Payment.objects.create(
            job=job,
            amount=amount,
            method=method,
            bank_account_id=bank_account_id,
            reference_number=reference,
            is_deposit=is_deposit,
            received_by=request.user,
            notes=request.POST.get("notes", ""),
        )
        return redirect("payments:pay", job_id=job_id)

    return render(
        request,
        "payments/screen.html",
        {
            "job": job,
            "bank_accounts": bank_accounts,
            "existing_payments": existing_payments,
            "payment_methods": PaymentMethod.choices,
        },
    )


@login_required
def payment_receipt(request, job_id):
    """Redirect to document receipt PDF for this job."""
    job = get_object_or_404(Job, pk=job_id)
    # Find or create receipt document — handled by documents app
    from documents.views import get_or_create_receipt

    doc = get_or_create_receipt(job, created_by=request.user)
    return redirect("documents:pdf", pk=doc.pk)


@role_required(Role.COUNTER, Role.OWNER)
def generate_promptpay_qr(request):
    """
    HTMX endpoint: generate PromptPay QR PNG and return as base64 img tag.
    Called when payment method changes to PromptPay with an amount.
    """
    try:
        amount = float(request.GET.get("amount", 0))
        promptpay_id = request.GET.get("promptpay_id", "")
    except (ValueError, TypeError):
        return HttpResponse("", status=400)

    if not promptpay_id or amount <= 0:
        return HttpResponse("")

    try:
        import qrcode
        from promptpay import qrcode as ppqr

        payload = ppqr.generate_payload(promptpay_id, amount=amount)
        img = qrcode.make(payload)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode()
        return HttpResponse(
            f'<img src="data:image/png;base64,{b64}" alt="PromptPay QR" class="w-48 h-48 mx-auto">',
        )
    except Exception:
        return HttpResponse('<p class="text-red-500">ไม่สามารถสร้าง QR Code ได้</p>')
