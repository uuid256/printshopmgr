"""Owner/manager dashboard — revenue summary, pipeline counts, overdue alerts."""

from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.shortcuts import render
from django.utils import timezone

from jobs.models import Job, JobStatus, PaymentStatus

# Ordered list of operational statuses shown in pipeline summary
PIPELINE_STATUSES = [
    JobStatus.PENDING,
    JobStatus.DESIGNING,
    JobStatus.AWAITING_APPROVAL,
    JobStatus.APPROVED,
    JobStatus.PRINTING,
    JobStatus.CUTTING,
    JobStatus.LAMINATING,
    JobStatus.READY,
]


@login_required
def dashboard(request):
    today = timezone.localdate()
    month_start = today.replace(day=1)

    # Revenue this month (completed + paid)
    monthly_revenue = (
        Job.objects.filter(
            status=JobStatus.COMPLETED,
            payment_status=PaymentStatus.PAID,
            updated_at__date__gte=month_start,
        ).aggregate(total=Sum("quoted_price"))["total"]
        or Decimal("0")
    )

    # Pipeline counts — only active statuses, with Thai display labels
    raw_counts = {
        item["status"]: item["count"]
        for item in (
            Job.objects.filter(status__in=PIPELINE_STATUSES)
            .values("status")
            .annotate(count=Count("id"))
        )
    }
    # Build ordered list with (label, count) so template can iterate cleanly
    pipeline_rows = [
        {"label": JobStatus(s).label, "count": raw_counts.get(s, 0), "status": s}
        for s in PIPELINE_STATUSES
        if raw_counts.get(s, 0) > 0  # only show statuses that have jobs
    ]

    # Overdue: past due date, still in progress
    overdue_jobs = (
        Job.objects.filter(
            due_date__lt=today,
            status__in=[
                JobStatus.PENDING, JobStatus.DESIGNING, JobStatus.AWAITING_APPROVAL,
                JobStatus.PRINTING, JobStatus.CUTTING, JobStatus.LAMINATING,
            ],
        )
        .select_related("customer")
        .order_by("due_date")[:10]
    )

    # Outstanding: unpaid or partially paid, not cancelled
    outstanding = (
        Job.objects.filter(payment_status__in=[PaymentStatus.UNPAID, PaymentStatus.PARTIAL])
        .exclude(status=JobStatus.CANCELLED)
        .aggregate(total=Sum("quoted_price"))["total"]
        or Decimal("0")
    )

    return render(
        request,
        "dashboard/home.html",
        {
            "monthly_revenue": monthly_revenue,
            "pipeline_rows": pipeline_rows,
            "pending_count": raw_counts.get(JobStatus.PENDING, 0),
            "ready_count": raw_counts.get(JobStatus.READY, 0),
            "overdue_jobs": overdue_jobs,
            "outstanding": outstanding,
            "today": today,
        },
    )
