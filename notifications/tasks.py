"""
Celery scheduled tasks for automated notifications.

All tasks check the relevant kill-switch Setting before sending.
Tasks are registered in CELERY_BEAT_SCHEDULE (settings.py) and run via celery-beat.

Schedule:
  08:00  send_daily_summary
  09:00  send_payment_reminders
  09:05  send_material_alerts
  10:00  send_approval_reminders
"""

import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Count
from django.utils import timezone

logger = logging.getLogger(__name__)


def _get_setting(key, default=""):
    """Read a Setting value. Imported lazily to avoid early-load issues."""
    from documents.models import Setting

    return Setting.get(key, default)


def _line_enabled():
    return _get_setting("notification_line_enabled", "0") == "1"


def _email_enabled():
    return _get_setting("notification_email_enabled", "0") == "1"


def _email_recipient():
    return _get_setting("notification_email_recipient", "").strip()


def _push_owner_line(text):
    """Push a text message to all owner users who have line_user_id set."""
    from accounts.models import Role, User

    owners = User.objects.filter(role=Role.OWNER).exclude(line_user_id="")
    for owner in owners:
        _push_line(owner.line_user_id, text)


def _push_line(line_user_id, text, job=None, message_type="daily_summary"):
    """Push a LINE message and log the result."""
    token = getattr(settings, "LINE_CHANNEL_ACCESS_TOKEN", "")
    if not token:
        return

    from .models import NotificationLog

    success = True
    error_message = ""

    try:
        from linebot.v3.messaging import (
            ApiClient,
            Configuration,
            MessagingApi,
            PushMessageRequest,
            TextMessage,
        )

        configuration = Configuration(access_token=token)
        with ApiClient(configuration) as api_client:
            api = MessagingApi(api_client)
            api.push_message(
                PushMessageRequest(
                    to=line_user_id,
                    messages=[TextMessage(text=text)],
                )
            )
    except Exception as exc:
        success = False
        error_message = str(exc)
        logger.warning("LINE push failed for %s: %s", line_user_id, exc)

    NotificationLog.objects.create(
        job=job,
        line_user_id=line_user_id,
        message_type=message_type,
        success=success,
        error_message=error_message,
    )


def _send_email(subject, body):
    """Send an email to the configured owner recipient."""
    recipient = _email_recipient()
    if not recipient:
        return
    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
        )
    except Exception as exc:
        logger.warning("Email send failed (subject=%r): %s", subject, exc)


# ---------------------------------------------------------------------------
# Task A — Daily Summary
# ---------------------------------------------------------------------------

@shared_task(name="notifications.tasks.send_daily_summary")
def send_daily_summary():
    """Aggregate job counts and overdue payments, then notify owner."""
    line_on = _line_enabled()
    email_on = _email_enabled()
    if not line_on and not email_on:
        return "disabled"

    from jobs.models import Job, JobStatus, PaymentStatus

    today = timezone.localdate()

    active_statuses = [
        JobStatus.PENDING,
        JobStatus.DESIGNING,
        JobStatus.AWAITING_APPROVAL,
        JobStatus.REVISION,
        JobStatus.APPROVED,
        JobStatus.PRINTING,
        JobStatus.CUTTING,
        JobStatus.LAMINATING,
        JobStatus.READY,
    ]

    # Jobs by status
    counts = {
        row["status"]: row["count"]
        for row in Job.objects.filter(status__in=active_statuses)
        .values("status")
        .annotate(count=Count("id"))
    }

    # Due today
    due_today = Job.objects.filter(due_date=today, status__in=active_statuses).count()

    # Overdue unpaid
    overdue = Job.objects.filter(
        payment_status__in=[PaymentStatus.UNPAID, PaymentStatus.PARTIAL],
        status__in=[JobStatus.READY, JobStatus.COMPLETED],
    ).count()

    lines = [
        f"📊 สรุปประจำวัน {today.strftime('%d/%m/%Y')}",
        "",
    ]
    for status in active_statuses:
        count = counts.get(status, 0)
        if count:
            from jobs.models import JobStatus as JS

            label = JS(status).label
            lines.append(f"  {label}: {count} งาน")

    lines += [
        "",
        f"📅 ครบกำหนดวันนี้: {due_today} งาน",
        f"⚠️ ค้างชำระ (พร้อมส่ง/เสร็จ): {overdue} งาน",
    ]

    text = "\n".join(lines)

    if line_on:
        _push_owner_line(text)
    if email_on:
        _send_email(f"[Print Shop] สรุปประจำวัน {today.strftime('%d/%m/%Y')}", text)

    return f"daily_summary sent: {today}"


# ---------------------------------------------------------------------------
# Task B — Payment Reminders
# ---------------------------------------------------------------------------

@shared_task(name="notifications.tasks.send_payment_reminders")
def send_payment_reminders():
    """Send payment reminders to customers with overdue unpaid jobs."""
    if not _line_enabled():
        return "disabled"

    from jobs.models import Job, JobStatus, PaymentStatus

    reminder_days = int(_get_setting("payment_reminder_days", "1"))
    today = timezone.localdate()
    cutoff = today - timezone.timedelta(days=reminder_days)

    # Jobs that are ready/completed, have balance due, and due_date has passed
    jobs = (
        Job.objects.filter(
            payment_status__in=[PaymentStatus.UNPAID, PaymentStatus.PARTIAL],
            status__in=[JobStatus.READY, JobStatus.COMPLETED],
            due_date__lte=cutoff,
        )
        .select_related("customer")
        .prefetch_related("customer__line_binding")
    )

    base_url = getattr(settings, "BASE_URL", "")
    sent = 0

    for job in jobs:
        try:
            binding = job.customer.line_binding
        except Exception:
            continue

        tracking_url = f"{base_url}{job.get_tracking_url()}"
        text = (
            f"💳 แจ้งเตือนชำระเงิน\n"
            f"งาน: #{job.pk} {job.title}\n"
            f"ยอดคงเหลือ: ฿{job.balance_due:,.2f}\n"
            f"ดูรายละเอียด: {tracking_url}"
        )

        _push_line(
            line_user_id=binding.line_user_id,
            text=text,
            job=job,
            message_type="payment_reminder",
        )
        sent += 1

    return f"payment_reminders sent: {sent}"


# ---------------------------------------------------------------------------
# Task C — Material Alerts
# ---------------------------------------------------------------------------

@shared_task(name="notifications.tasks.send_material_alerts")
def send_material_alerts():
    """Alert owner about low-stock materials (LINE + email, debounced 24h)."""
    line_on = _line_enabled()
    email_on = _email_enabled()
    if not line_on and not email_on:
        return "disabled"

    from production.models import Material
    from .models import NotificationLog

    low_stock = [m for m in Material.objects.filter(is_active=True) if m.is_low_stock]
    if not low_stock:
        return "no low stock"

    now = timezone.now()
    cutoff_24h = now - timezone.timedelta(hours=24)
    sent = 0

    for material in low_stock:
        # Debounce: skip if we already sent an alert for this material in the last 24h
        # We store the material name in error_message (job=None) for identification.
        already_sent = NotificationLog.objects.filter(
            job=None,
            message_type="daily_summary",  # reuse type; identified by error_message
            error_message=f"material_alert:{material.pk}",
            sent_at__gte=cutoff_24h,
        ).exists()
        if already_sent:
            continue

        text = (
            f"⚠️ วัสดุใกล้หมด\n"
            f"{material.name}: {material.quantity_in_stock} {material.unit} "
            f"(ขั้นต่ำ: {material.min_quantity} {material.unit})"
        )

        if line_on:
            _push_owner_line(text)
        if email_on:
            _send_email(f"[Print Shop] วัสดุใกล้หมด: {material.name}", text)

        # Log the alert with material ID in error_message for debounce lookup
        NotificationLog.objects.create(
            job=None,
            line_user_id="system",
            message_type="daily_summary",
            success=True,
            error_message=f"material_alert:{material.pk}",
        )
        sent += 1

    return f"material_alerts sent: {sent}"


# ---------------------------------------------------------------------------
# Task D — Approval Reminders
# ---------------------------------------------------------------------------

@shared_task(name="notifications.tasks.send_approval_reminders")
def send_approval_reminders():
    """Remind customers whose proof has been waiting for approval too long."""
    if not _line_enabled():
        return "disabled"

    from jobs.models import Job, JobStatus, JobStatusHistory

    reminder_days = int(_get_setting("approval_reminder_days", "3"))
    cutoff = timezone.now() - timezone.timedelta(days=reminder_days)

    # Find jobs stuck in AWAITING_APPROVAL where the last status change is old enough
    awaiting_jobs = (
        Job.objects.filter(status=JobStatus.AWAITING_APPROVAL)
        .select_related("customer")
        .prefetch_related("customer__line_binding")
    )

    base_url = getattr(settings, "BASE_URL", "")
    sent = 0

    for job in awaiting_jobs:
        # Check when the job entered AWAITING_APPROVAL
        last_transition = (
            JobStatusHistory.objects.filter(
                job=job,
                to_status=JobStatus.AWAITING_APPROVAL,
            )
            .order_by("-changed_at")
            .first()
        )
        if not last_transition or last_transition.changed_at > cutoff:
            continue

        try:
            binding = job.customer.line_binding
        except Exception:
            continue

        tracking_url = f"{base_url}{job.get_tracking_url()}"
        text = (
            f"🎨 กรุณาตรวจสอบและอนุมัติแบบ\n"
            f"งาน: #{job.pk} {job.title}\n"
            f"รออนุมัติมา {reminder_days} วันแล้ว\n"
            f"กรุณาอนุมัติที่: {tracking_url}"
        )

        _push_line(
            line_user_id=binding.line_user_id,
            text=text,
            job=job,
            message_type="approval_reminder",
        )
        sent += 1

    return f"approval_reminders sent: {sent}"
