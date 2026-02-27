"""
Notification views — LINE webhook handler and settings page.
"""

import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)

# Setting keys managed on the notifications settings page
SETTING_KEYS = [
    "notification_email_enabled",
    "notification_line_enabled",
    "notification_email_recipient",
    "payment_reminder_days",
    "approval_reminder_days",
]

SETTING_DEFAULTS = {
    "notification_email_enabled": "0",
    "notification_line_enabled": "0",
    "notification_email_recipient": "",
    "payment_reminder_days": "1",
    "approval_reminder_days": "3",
}


def _owner_required(request):
    """Raise PermissionDenied if the user is not an owner."""
    if not (request.user.is_authenticated and (request.user.is_superuser or request.user.is_owner)):
        raise PermissionDenied


@login_required
def notification_settings(request):
    """Owner-only settings page for email/LINE kill switches and thresholds."""
    _owner_required(request)

    from documents.models import Setting
    from .models import CustomerLineBinding

    if request.method == "POST":
        for key in SETTING_KEYS:
            if key in ("notification_email_enabled", "notification_line_enabled"):
                value = "1" if request.POST.get(key) == "1" else "0"
            else:
                value = request.POST.get(key, SETTING_DEFAULTS.get(key, "")).strip()
            Setting.objects.update_or_create(key=key, defaults={"value": value})
        messages.success(request, "บันทึกการตั้งค่าแล้ว")

    current = {key: Setting.get(key, SETTING_DEFAULTS.get(key, "")) for key in SETTING_KEYS}
    line_customer_count = CustomerLineBinding.objects.filter(customer__isnull=False).count()

    return render(request, "notifications/settings.html", {
        "s": current,
        "line_customer_count": line_customer_count,
    })


@login_required
@require_POST
def send_test_email(request):
    """HTMX endpoint — send a test email to the configured recipient."""
    _owner_required(request)

    from documents.models import Setting

    if Setting.get("notification_email_enabled", "0") != "1":
        return HttpResponse(
            '<span class="text-red-600 text-sm">อีเมลยังไม่ได้เปิดใช้งาน</span>'
        )

    recipient = Setting.get("notification_email_recipient", "").strip()
    if not recipient:
        return HttpResponse(
            '<span class="text-red-600 text-sm">ยังไม่ได้ระบุอีเมลผู้รับ</span>'
        )

    try:
        send_mail(
            subject="[Print Shop] ทดสอบการแจ้งเตือนอีเมล",
            message="อีเมลนี้เป็นการทดสอบระบบแจ้งเตือน Print Shop Manager\n\nหากคุณได้รับอีเมลนี้ แสดงว่าการตั้งค่า SMTP ถูกต้องแล้ว",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
        )
        return HttpResponse(
            f'<span class="text-green-600 text-sm">ส่งอีเมลทดสอบไปที่ {recipient} แล้ว</span>'
        )
    except Exception as exc:
        logger.warning("Test email failed: %s", exc)
        return HttpResponse(
            f'<span class="text-red-600 text-sm">ส่งอีเมลไม่สำเร็จ: {exc}</span>'
        )


@csrf_exempt
@require_POST
def line_webhook(request):
    """Receive and process LINE webhook events."""
    channel_secret = getattr(settings, "LINE_CHANNEL_SECRET", "")
    if not channel_secret:
        return HttpResponse("LINE not configured", status=503)

    signature = request.META.get("HTTP_X_LINE_SIGNATURE", "")
    body = request.body.decode("utf-8")

    try:
        from linebot.v3 import WebhookParser
        from linebot.v3.exceptions import InvalidSignatureError
        from linebot.v3.webhooks.models import FollowEvent, UnfollowEvent

        parser = WebhookParser(channel_secret)
        try:
            events = parser.parse(body, signature)
        except InvalidSignatureError:
            logger.warning("LINE webhook: invalid signature")
            return HttpResponse("Invalid signature", status=400)

        for event in events:
            line_user_id = event.source.user_id if event.source else None
            if not line_user_id:
                continue

            if isinstance(event, FollowEvent):
                _handle_follow(line_user_id)
            elif isinstance(event, UnfollowEvent):
                _handle_unfollow(line_user_id)

    except Exception as exc:
        logger.exception("LINE webhook processing error: %s", exc)
        return HttpResponse("Error", status=500)

    return HttpResponse("OK")


def _handle_follow(line_user_id):
    """Create or restore a CustomerLineBinding when user follows the bot."""
    from .models import CustomerLineBinding

    CustomerLineBinding.objects.get_or_create(line_user_id=line_user_id)
    logger.info("LINE follow: %s", line_user_id)


def _handle_unfollow(line_user_id):
    """Remove CustomerLineBinding when user blocks/unfollows the bot."""
    from .models import CustomerLineBinding

    CustomerLineBinding.objects.filter(line_user_id=line_user_id).delete()
    logger.info("LINE unfollow: %s", line_user_id)
