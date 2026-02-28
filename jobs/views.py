"""Job views — list, create wizard, detail, status transitions, file uploads, kanban."""

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.mixins import role_required
from accounts.models import Role

from .models import Job, JobFile, JobStatus


@login_required
def job_list(request):
    status_filter = request.GET.get("status", "")
    q = request.GET.get("q", "").strip()
    jobs = Job.objects.select_related("customer", "product_type").order_by("-created_at")
    if status_filter:
        jobs = jobs.filter(status=status_filter)
    if q:
        jobs = jobs.filter(
            Q(title__icontains=q)
            | Q(customer__name__icontains=q)
            | Q(customer__phone__icontains=q)
        )
    return render(
        request,
        "jobs/list.html",
        {
            "jobs": jobs,
            "status_filter": status_filter,
            "all_statuses": JobStatus.choices,
            "today": timezone.localdate(),
            "q": q,
        },
    )


@login_required
def job_slip_pdf(request, pk):
    """Generate an A5 job slip PDF with QR code for the customer tracking URL."""
    import base64
    import io

    import qrcode
    from django.template.loader import render_to_string
    from weasyprint import HTML

    from documents.models import Setting

    job = get_object_or_404(
        Job.objects.select_related("customer", "product_type"),
        pk=pk,
    )
    shop_info = {k: Setting.get(k, "") for k in ["shop_name", "shop_address", "shop_phone"]}
    tracking_url = request.build_absolute_uri(job.get_tracking_url())
    buf = io.BytesIO()
    qrcode.make(tracking_url).save(buf, format="PNG")
    qr_b64 = base64.b64encode(buf.getvalue()).decode()
    html_string = render_to_string(
        "jobs/pdf/job_slip.html",
        {"job": job, "shop": shop_info, "qr_b64": qr_b64},
        request=request,
    )
    pdf = HTML(string=html_string, base_url=request.build_absolute_uri("/")).write_pdf()
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="job_{job.pk}_slip.pdf"'
    return response


@login_required
def job_detail(request, pk):
    job = get_object_or_404(
        Job.objects.select_related("customer", "product_type", "assigned_designer"),
        pk=pk,
    )
    history = job.status_history.select_related("changed_by").order_by("-changed_at")
    files = job.files.select_related("uploaded_by")
    return render(request, "jobs/detail.html", {
        "job": job,
        "history": history,
        "files": files,
        "today": timezone.localdate(),
    })


@role_required(Role.COUNTER, Role.OWNER)
def job_create(request):
    """4-step job creation: customer → product → details → confirm."""
    from .forms import JobCreateForm

    if request.method == "POST":
        form = JobCreateForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.created_by = request.user
            job.save()
            return redirect("jobs:detail", pk=job.pk)
    else:
        form = JobCreateForm(initial={"customer": request.GET.get("customer")})
    return render(request, "jobs/create.html", {"form": form})


@role_required(Role.COUNTER, Role.OWNER)
def job_reorder(request, pk):
    """Pre-fill the job creation form from an existing job."""
    from .forms import JobCreateForm

    source = get_object_or_404(Job.objects.select_related("customer", "product_type", "assigned_designer"), pk=pk)
    copy_fields = [
        "title", "description", "quantity", "width_cm", "height_cm",
        "quoted_price", "deposit_amount", "discount_amount", "internal_notes",
    ]
    initial = {field: getattr(source, field) for field in copy_fields}
    initial["customer"] = source.customer_id
    initial["product_type"] = source.product_type_id
    if source.assigned_designer_id:
        initial["assigned_designer"] = source.assigned_designer_id
    form = JobCreateForm(initial=initial)
    return render(request, "jobs/create.html", {"form": form, "reorder_source": source})


@role_required(Role.COUNTER, Role.OWNER)
def job_edit(request, pk):
    from .forms import JobCreateForm

    job = get_object_or_404(Job, pk=pk)
    if request.method == "POST":
        form = JobCreateForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            return redirect("jobs:detail", pk=job.pk)
    else:
        form = JobCreateForm(instance=job)
    return render(request, "jobs/create.html", {"form": form, "job": job})


@login_required
def job_update_status(request, pk):
    """HTMX endpoint: transition job status."""
    if request.method != "POST":
        return HttpResponse(status=405)

    job = get_object_or_404(Job, pk=pk)
    new_status = request.POST.get("status")
    note = request.POST.get("note", "")

    try:
        job.transition_to(new_status, changed_by=request.user, note=note)
    except ValueError as e:
        return HttpResponse(str(e), status=400)

    from django.conf import settings as django_settings
    if getattr(django_settings, "LINE_CHANNEL_ACCESS_TOKEN", ""):
        try:
            from notifications.service import send_status_notification
            send_status_notification(job)
        except Exception:
            pass

    # In-app notifications for creator and assigned designer
    try:
        from notifications.models import Notification
        recipients = set()
        if hasattr(job, "created_by_id") and job.created_by_id:
            recipients.add(job.created_by_id)
        if job.assigned_designer_id:
            recipients.add(job.assigned_designer_id)
        for uid in recipients:
            Notification.objects.create(
                user_id=uid,
                job=job,
                title=f"งาน #{job.pk} เปลี่ยนสถานะ → {job.get_status_display()}",
                notif_type=Notification.Type.STATUS_CHANGE,
            )
    except Exception:
        pass

    # Return updated status badge partial for HTMX swap
    return render(request, "jobs/partials/status_badge.html", {"job": job})


@login_required
def job_file_upload(request, pk):
    """HTMX endpoint: upload a file to a job. Returns file_card partial."""
    if request.method != "POST":
        return HttpResponse(status=405)

    job = get_object_or_404(Job, pk=pk)
    uploaded_file = request.FILES.get("file")
    if not uploaded_file:
        return HttpResponse("ไม่พบไฟล์", status=400)

    if uploaded_file.size > 20 * 1024 * 1024:
        return HttpResponse("ไฟล์ใหญ่เกิน 20 MB", status=400)

    allowed_content_types = {
        "image/jpeg", "image/png", "image/gif", "image/webp", "application/pdf",
    }
    if uploaded_file.content_type not in allowed_content_types:
        return HttpResponse("ประเภทไฟล์ไม่รองรับ (รองรับ image/*, PDF)", status=400)

    file_type = request.POST.get("file_type", JobFile.FileType.ARTWORK)
    job_file = JobFile.objects.create(
        job=job,
        file=uploaded_file,
        file_type=file_type,
        uploaded_by=request.user,
        notes=request.POST.get("notes", ""),
    )

    if file_type == JobFile.FileType.PROOF:
        from django.conf import settings as django_settings
        if getattr(django_settings, "LINE_CHANNEL_ACCESS_TOKEN", ""):
            try:
                from notifications.service import send_proof_ready_notification
                send_proof_ready_notification(job)
            except Exception:
                pass

    return render(request, "jobs/partials/file_card.html", {"file": job_file, "job": job})


@login_required
def job_file_delete(request, pk, file_pk):
    """HTMX endpoint: delete a file. Returns empty 200 so HTMX removes the card."""
    if request.method != "POST":
        return HttpResponse(status=405)

    job = get_object_or_404(Job, pk=pk)
    job_file = get_object_or_404(JobFile, pk=file_pk, job=job)

    if request.user != job_file.uploaded_by and not request.user.has_any_role(
        Role.OWNER, Role.COUNTER
    ):
        raise PermissionDenied

    job_file.file.delete(save=False)
    job_file.delete()
    return HttpResponse("")


@role_required(Role.DESIGNER, Role.COUNTER, Role.OWNER)
def design_kanban(request):
    """Designer Kanban board — 3 columns: designing, awaiting_approval, revision."""
    kanban_statuses = [JobStatus.DESIGNING, JobStatus.AWAITING_APPROVAL, JobStatus.REVISION]

    jobs_qs = (
        Job.objects.filter(status__in=kanban_statuses)
        .select_related("customer", "assigned_designer")
        .prefetch_related("files")
        .order_by("due_date", "created_at")
    )

    if request.user.role == Role.DESIGNER:
        jobs_qs = jobs_qs.filter(assigned_designer=request.user)

    columns_map = {s: [] for s in kanban_statuses}
    for job in jobs_qs:
        columns_map[job.status].append(job)

    columns = [
        {
            "status": JobStatus.DESIGNING,
            "label": JobStatus.DESIGNING.label,
            "jobs": columns_map[JobStatus.DESIGNING],
            "color": "blue",
        },
        {
            "status": JobStatus.AWAITING_APPROVAL,
            "label": JobStatus.AWAITING_APPROVAL.label,
            "jobs": columns_map[JobStatus.AWAITING_APPROVAL],
            "color": "yellow",
        },
        {
            "status": JobStatus.REVISION,
            "label": JobStatus.REVISION.label,
            "jobs": columns_map[JobStatus.REVISION],
            "color": "orange",
        },
    ]

    return render(request, "jobs/kanban.html", {"columns": columns, "today": timezone.localdate()})


@login_required
def calculate_price(request):
    """
    HTMX endpoint: real-time price calculation.
    Called on product_type, quantity, width, height change.
    """
    from decimal import Decimal

    from production.models import ProductType

    try:
        product_type_id = int(request.GET.get("product_type", 0))
        quantity = int(request.GET.get("quantity", 1))
        width = Decimal(request.GET.get("width", 0) or 0)
        height = Decimal(request.GET.get("height", 0) or 0)
    except (ValueError, TypeError):
        return HttpResponse("0", status=400)

    try:
        pt = ProductType.objects.get(pk=product_type_id, is_active=True)
    except ProductType.DoesNotExist:
        return render(request, "jobs/partials/price_display.html", {"price": 0})

    if pt.pricing_method == "per_sqm":
        sqm = (width / 100) * (height / 100)  # cm → m²
        price = pt.base_price * sqm * quantity
    elif pt.pricing_method == "per_unit":
        price = pt.base_price * quantity
    else:  # flat
        price = pt.base_price

    return render(request, "jobs/partials/price_display.html", {"price": price})
