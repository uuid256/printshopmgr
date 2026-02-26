"""Document views — list, detail, PDF generation via WeasyPrint."""

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string

from accounts.mixins import role_required
from accounts.models import Role
from jobs.models import Job

from .models import Document, DocumentItem, DocumentType, Setting


@login_required
def document_list(request):
    doc_type = request.GET.get("type", "")
    docs = Document.objects.filter(is_void=False).select_related("job__customer").order_by("-issued_at")
    if doc_type:
        docs = docs.filter(document_type=doc_type)
    return render(
        request,
        "documents/list.html",
        {"documents": docs, "doc_type": doc_type, "document_types": DocumentType.choices},
    )


@login_required
def document_detail(request, pk):
    doc = get_object_or_404(Document.objects.select_related("job__customer", "issued_by"), pk=pk)
    return render(request, "documents/detail.html", {"document": doc})


@login_required
def document_pdf(request, pk):
    """Generate PDF via WeasyPrint and stream to browser."""
    from weasyprint import HTML

    doc = get_object_or_404(Document.objects.prefetch_related("items").select_related("issued_by"), pk=pk)
    shop_info = {
        "name": Setting.get("shop_name", "ร้านพิมพ์"),
        "address": Setting.get("shop_address", ""),
        "tax_id": Setting.get("shop_tax_id", ""),
        "phone": Setting.get("shop_phone", ""),
    }
    html_string = render_to_string(
        "documents/pdf/document.html",
        {"document": doc, "shop": shop_info},
        request=request,
    )
    pdf_bytes = HTML(string=html_string, base_url=request.build_absolute_uri("/")).write_pdf()
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{doc.document_number}.pdf"'
    return response


@role_required(Role.COUNTER, Role.OWNER)
def create_quotation(request, job_id):
    """Create a quotation document for a job."""
    job = get_object_or_404(Job.objects.select_related("customer"), pk=job_id)

    doc = Document.objects.create(
        job=job,
        document_type=DocumentType.QUOTATION,
        customer_name=job.customer.name,
        customer_address=job.customer.billing_address,
        customer_tax_id=job.customer.tax_id,
        subtotal=job.quoted_price - job.discount_amount,
        vat_rate=0,
        vat_amount=0,
        total_amount=job.quoted_price - job.discount_amount,
        issued_by=request.user,
    )
    DocumentItem.objects.create(
        document=doc,
        description=f"{job.product_type.name} — {job.title}",
        quantity=job.quantity,
        unit=job.product_type.unit,
        unit_price=(job.quoted_price - job.discount_amount) / max(job.quantity, 1),
    )
    return redirect("documents:pdf", pk=doc.pk)


def get_or_create_receipt(job, created_by):
    """
    Get existing receipt for job or create one.
    Called from payments.views after payment recorded.
    """
    existing = Document.objects.filter(
        job=job,
        document_type=DocumentType.RECEIPT,
        is_void=False,
    ).first()
    if existing:
        return existing

    total = job.quoted_price - job.discount_amount
    doc = Document.objects.create(
        job=job,
        document_type=DocumentType.RECEIPT,
        customer_name=job.customer.name,
        customer_address=job.customer.billing_address,
        customer_tax_id=job.customer.tax_id,
        subtotal=total,
        vat_rate=0,
        vat_amount=0,
        total_amount=total,
        issued_by=created_by,
    )
    DocumentItem.objects.create(
        document=doc,
        description=f"{job.product_type.name} — {job.title}",
        quantity=job.quantity,
        unit=job.product_type.unit,
        unit_price=total / max(job.quantity, 1),
    )
    return doc
