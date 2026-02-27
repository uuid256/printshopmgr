"""
Public (no-login) customer-facing views.

The tracking page lets customers check job status via a UUID URL —
no account required.
"""

from django.shortcuts import get_object_or_404, redirect, render

from jobs.models import Job, JobApproval, JobFile, JobStatus


def job_tracking(request, token):
    """Public job status page — accessible via unique URL, no login required."""
    job = get_object_or_404(
        Job.objects.select_related("customer", "product_type").prefetch_related("files"),
        tracking_token=token,
    )
    history = job.status_history.order_by("-changed_at")[:5]
    proof_files = [f for f in job.files.all() if f.file_type == JobFile.FileType.PROOF]
    last_approval = job.approvals.order_by("-decided_at").first()

    context = {
        "job": job,
        "history": history,
        "proof_files": proof_files,
        "last_approval": last_approval,
        "approved": request.GET.get("approved") == "1",
        "revised": request.GET.get("revised") == "1",
    }
    return render(request, "public/tracking.html", context)


def job_approve(request, token):
    """POST: customer approves the proof via public tracking URL."""
    if request.method != "POST":
        from django.http import HttpResponse
        return HttpResponse(status=405)

    job = get_object_or_404(
        Job.objects.select_related("customer").prefetch_related("files"),
        tracking_token=token,
    )

    if job.status != JobStatus.AWAITING_APPROVAL:
        return redirect("public:track", token=token)

    proof_file = next(
        (f for f in job.files.all() if f.file_type == JobFile.FileType.PROOF), None
    )

    JobApproval.objects.create(
        job=job,
        proof_file=proof_file,
        decision=JobApproval.Decision.APPROVED,
        decided_by_customer=True,
        approved_by_name=request.POST.get("customer_name", ""),
        approved_by_ip=request.META.get("REMOTE_ADDR"),
    )

    try:
        job.transition_to(
            JobStatus.APPROVED,
            changed_by=None,
            note="ลูกค้าอนุมัติผ่านลิงก์ติดตาม",
        )
    except ValueError:
        pass

    from django.conf import settings as django_settings
    if getattr(django_settings, "LINE_CHANNEL_ACCESS_TOKEN", ""):
        try:
            from notifications.service import send_status_notification
            send_status_notification(job)
        except Exception:
            pass

    return redirect(f"{job.get_tracking_url()}?approved=1")


def job_request_revision(request, token):
    """POST: customer requests revision via public tracking URL."""
    if request.method != "POST":
        from django.http import HttpResponse
        return HttpResponse(status=405)

    job = get_object_or_404(
        Job.objects.select_related("customer").prefetch_related("files"),
        tracking_token=token,
    )

    if job.status != JobStatus.AWAITING_APPROVAL:
        return redirect("public:track", token=token)

    proof_file = next(
        (f for f in job.files.all() if f.file_type == JobFile.FileType.PROOF), None
    )
    notes = request.POST.get("notes", "")

    JobApproval.objects.create(
        job=job,
        proof_file=proof_file,
        decision=JobApproval.Decision.REVISION,
        decided_by_customer=True,
        revision_notes=notes,
        approved_by_name=request.POST.get("customer_name", ""),
        approved_by_ip=request.META.get("REMOTE_ADDR"),
    )

    try:
        job.transition_to(
            JobStatus.REVISION,
            changed_by=None,
            note=f"ลูกค้าขอแก้ไข: {notes}" if notes else "ลูกค้าขอแก้ไขผ่านลิงก์ติดตาม",
        )
    except ValueError:
        pass

    from django.conf import settings as django_settings
    if getattr(django_settings, "LINE_CHANNEL_ACCESS_TOKEN", ""):
        try:
            from notifications.service import send_status_notification
            send_status_notification(job)
        except Exception:
            pass

    return redirect(f"{job.get_tracking_url()}?revised=1")
