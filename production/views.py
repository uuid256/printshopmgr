"""Production queue views — mobile-first for operators."""

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from accounts.mixins import role_required
from accounts.models import Role
from jobs.models import Job, JobStatus


@login_required
def production_queue(request):
    """
    Mobile-first production queue.
    Shows jobs in PRINTING and CUTTING status, ordered by created date.
    """
    jobs = (
        Job.objects.filter(status__in=[JobStatus.PRINTING, JobStatus.CUTTING, JobStatus.LAMINATING])
        .select_related("customer", "product_type")
        .order_by("created_at")
    )
    return render(request, "production/queue.html", {"jobs": jobs})


@role_required(Role.OPERATOR, Role.OWNER)
def update_job_status(request, job_id):
    """HTMX endpoint: advance job to next status from production queue."""
    if request.method != "POST":
        return HttpResponse(status=405)

    job = get_object_or_404(Job, pk=job_id)
    new_status = request.POST.get("status")

    # Validate the transition is allowed from production
    production_statuses = {JobStatus.PRINTING, JobStatus.CUTTING, JobStatus.LAMINATING, JobStatus.READY}
    if new_status not in production_statuses:
        return HttpResponse("Invalid status", status=400)

    job.transition_to(new_status, changed_by=request.user)
    return render(request, "production/partials/job_card.html", {"job": job})
