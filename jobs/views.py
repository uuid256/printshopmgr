"""Job views — list, create wizard, detail, status transitions."""

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.mixins import role_required
from accounts.models import Role

from .models import Job, JobStatus


@login_required
def job_list(request):
    status_filter = request.GET.get("status", "")
    jobs = Job.objects.select_related("customer", "product_type").order_by("-created_at")
    if status_filter:
        jobs = jobs.filter(status=status_filter)
    return render(
        request,
        "jobs/list.html",
        {"jobs": jobs, "status_filter": status_filter, "all_statuses": JobStatus.choices, "today": timezone.localdate()},
    )


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

    # Return updated status badge partial for HTMX swap
    return render(request, "jobs/partials/status_badge.html", {"job": job})


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
