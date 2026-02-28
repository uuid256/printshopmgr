"""
Notifications app — Phase 2: LINE Messaging API integration.

CustomerLineBinding links a Customer to their LINE user ID (set via follow event).
NotificationLog records every outgoing LINE message for audit/debugging.
Notification is an in-app notification for staff users.
"""

from django.conf import settings
from django.db import models


class CustomerLineBinding(models.Model):
    """Links a Customer record to a LINE user ID acquired via follow webhook."""

    customer = models.OneToOneField(
        "customers.Customer",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="line_binding",
        verbose_name="ลูกค้า",
    )
    line_user_id = models.CharField(max_length=50, unique=True, verbose_name="LINE User ID")
    display_name = models.CharField(max_length=100, blank=True, verbose_name="ชื่อ LINE")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "LINE Binding"
        verbose_name_plural = "LINE Bindings"

    def __str__(self):
        return f"{self.display_name or self.line_user_id} → {self.customer}"


class NotificationLog(models.Model):
    """Records every outgoing LINE message attempt."""

    class MessageType(models.TextChoices):
        STATUS_CHANGE = "status_change", "เปลี่ยนสถานะ"
        PROOF_READY = "proof_ready", "proof พร้อม"
        APPROVAL_REMINDER = "approval_reminder", "แจ้งเตือนอนุมัติ"
        PAYMENT_REMINDER = "payment_reminder", "แจ้งเตือนชำระเงิน"
        DAILY_SUMMARY = "daily_summary", "สรุปประจำวัน"

    job = models.ForeignKey(
        "jobs.Job",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notification_logs",
        verbose_name="งาน",
    )
    line_user_id = models.CharField(max_length=50, verbose_name="LINE User ID")
    message_type = models.CharField(
        max_length=20, choices=MessageType.choices, verbose_name="ประเภท"
    )
    sent_at = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)

    class Meta:
        verbose_name = "Notification Log"
        verbose_name_plural = "Notification Logs"
        ordering = ["-sent_at"]

    def __str__(self):
        status = "✓" if self.success else "✗"
        return f"{status} {self.get_message_type_display()} → {self.line_user_id}"


class Notification(models.Model):
    """In-app notification for staff users (status changes, payments, low stock)."""

    class Type(models.TextChoices):
        STATUS_CHANGE = "status_change", "เปลี่ยนสถานะ"
        PAYMENT = "payment", "ชำระเงิน"
        LOW_STOCK = "low_stock", "วัสดุใกล้หมด"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="ผู้รับ",
    )
    job = models.ForeignKey(
        "jobs.Job",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
        verbose_name="งาน",
    )
    title = models.CharField(max_length=200, verbose_name="หัวข้อ")
    message = models.TextField(blank=True, verbose_name="รายละเอียด")
    notif_type = models.CharField(
        max_length=20,
        choices=Type.choices,
        default=Type.STATUS_CHANGE,
        verbose_name="ประเภท",
    )
    is_read = models.BooleanField(default=False, db_index=True, verbose_name="อ่านแล้ว")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "การแจ้งเตือน"
        verbose_name_plural = "การแจ้งเตือน"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{'✓' if self.is_read else '●'} {self.title}"
