"""
LINE Messaging API notification helpers.

Callers should guard with:
    if settings.LINE_CHANNEL_ACCESS_TOKEN:
        send_status_notification(job)
"""

import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def _push_message(line_user_id, text, job=None, message_type="status_change"):
    """Push a text message to a LINE user and record the result."""
    token = getattr(settings, "LINE_CHANNEL_ACCESS_TOKEN", "")
    if not token:
        return

    from .models import NotificationLog

    success = True
    error_message = ""

    try:
        from linebot.v3.messaging import ApiClient, Configuration, MessagingApi, PushMessageRequest, TextMessage

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


def _get_binding_for_job(job):
    """Return CustomerLineBinding for a job's customer, or None."""
    from .models import CustomerLineBinding

    try:
        return job.customer.line_binding
    except CustomerLineBinding.DoesNotExist:
        return None


def send_status_notification(job):
    """Send a status-change notification to the customer bound to the job."""
    binding = _get_binding_for_job(job)
    if not binding:
        return

    base_url = getattr(settings, "BASE_URL", "")
    tracking_url = f"{base_url}{job.get_tracking_url()}"

    text = (
        f"🖨️ อัปเดตงานของคุณ\n"
        f"งาน: #{job.pk} {job.title}\n"
        f"สถานะ: {job.get_status_display()}\n"
        f"ดูรายละเอียด: {tracking_url}"
    )

    _push_message(
        line_user_id=binding.line_user_id,
        text=text,
        job=job,
        message_type="status_change",
    )


def send_proof_ready_notification(job):
    """Send a proof-ready notification so the customer can review and approve."""
    binding = _get_binding_for_job(job)
    if not binding:
        return

    base_url = getattr(settings, "BASE_URL", "")
    tracking_url = f"{base_url}{job.get_tracking_url()}"

    text = (
        f"🎨 proof ของคุณพร้อมแล้ว!\n"
        f"งาน: #{job.pk} {job.title}\n"
        f"กรุณาตรวจสอบและอนุมัติที่:\n"
        f"{tracking_url}"
    )

    _push_message(
        line_user_id=binding.line_user_id,
        text=text,
        job=job,
        message_type="proof_ready",
    )
