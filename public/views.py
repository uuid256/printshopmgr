"""
Public (no-login) customer-facing views.

The tracking page lets customers check job status via a UUID URL —
no account required.
"""

from django.shortcuts import get_object_or_404, render

from jobs.models import Job


def job_tracking(request, token):
    """Public job status page — accessible via unique URL, no login required."""
    job = get_object_or_404(
        Job.objects.select_related("customer", "product_type"),
        tracking_token=token,
    )
    history = job.status_history.order_by("-changed_at")[:5]
    return render(request, "public/tracking.html", {"job": job, "history": history})
