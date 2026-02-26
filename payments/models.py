"""
Payment models.

A job can have multiple payments (e.g., deposit + balance).
BankAccount is reference data managed via Admin.
"""

from django.conf import settings
from django.db import models


class PaymentMethod(models.TextChoices):
    CASH = "cash", "เงินสด"
    PROMPTPAY = "promptpay", "PromptPay"
    BANK_TRANSFER = "bank_transfer", "โอนผ่านธนาคาร"
    CREDIT_CARD = "credit_card", "บัตรเครดิต"
    CHEQUE = "cheque", "เช็ค"


class BankAccount(models.Model):
    """Shop's bank accounts — displayed on payment screen and invoices."""

    bank_name = models.CharField(max_length=100, verbose_name="ชื่อธนาคาร")
    account_name = models.CharField(max_length=150, verbose_name="ชื่อบัญชี")
    account_number = models.CharField(max_length=20, verbose_name="เลขที่บัญชี")
    promptpay_id = models.CharField(
        max_length=15,
        blank=True,
        verbose_name="เบอร์ PromptPay / เลขผู้เสียภาษี",
    )
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = "บัญชีธนาคาร"
        verbose_name_plural = "บัญชีธนาคาร"
        ordering = ["sort_order", "bank_name"]

    def __str__(self):
        return f"{self.bank_name} — {self.account_number} ({self.account_name})"


class Payment(models.Model):
    """
    A payment transaction.

    Linked to a Job. Multiple payments per job are supported
    to handle deposit + final balance workflows.
    """

    job = models.ForeignKey(
        "jobs.Job",
        on_delete=models.PROTECT,
        related_name="payments",
        verbose_name="งาน",
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="จำนวนเงิน")
    method = models.CharField(
        max_length=15,
        choices=PaymentMethod.choices,
        verbose_name="วิธีชำระ",
    )
    bank_account = models.ForeignKey(
        BankAccount,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="บัญชีที่รับโอน",
        help_text="Required for bank_transfer payments",
    )
    reference_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="เลขอ้างอิง",
        help_text="Slip number for bank transfer / PromptPay",
    )
    is_deposit = models.BooleanField(default=False, verbose_name="เป็นมัดจำ")
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name="รับเงินโดย",
    )
    received_at = models.DateTimeField(auto_now_add=True, verbose_name="วันที่รับ")
    notes = models.CharField(max_length=255, blank=True, verbose_name="หมายเหตุ")

    class Meta:
        verbose_name = "การชำระเงิน"
        verbose_name_plural = "การชำระเงิน"
        ordering = ["-received_at"]

    def __str__(self):
        return f"฿{self.amount:,.2f} ({self.get_method_display()}) — Job #{self.job_id}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._update_job_payment_status()

    def _update_job_payment_status(self):
        from jobs.models import PaymentStatus

        job = self.job
        total_paid = job.total_paid
        if total_paid <= 0:
            new_status = PaymentStatus.UNPAID
        elif total_paid >= (job.quoted_price - job.discount_amount):
            new_status = PaymentStatus.PAID
        else:
            new_status = PaymentStatus.PARTIAL

        if job.payment_status != new_status:
            job.payment_status = new_status
            job.save(update_fields=["payment_status", "updated_at"])
