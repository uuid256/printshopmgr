"""
Customer models.

Supports both walk-in individuals and corporate accounts.
Corporate customers have tax ID (เลขประจำตัวผู้เสียภาษี) for tax invoice generation.
"""

from django.db import models


class CustomerType(models.Model):
    """Reference data: VIP, Corporate, Walk-in, etc."""

    name = models.CharField(max_length=100, verbose_name="ประเภทลูกค้า")
    credit_days = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="เครดิต (วัน)",
        help_text="0 = ชำระทันที, 30 = Net30",
    )
    discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="ส่วนลด (%)",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "ประเภทลูกค้า"
        verbose_name_plural = "ประเภทลูกค้า"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Customer(models.Model):
    """A customer — individual or corporate."""

    customer_type = models.ForeignKey(
        CustomerType,
        on_delete=models.PROTECT,
        verbose_name="ประเภท",
    )
    name = models.CharField(max_length=200, verbose_name="ชื่อ / ชื่อบริษัท")
    phone = models.CharField(max_length=20, verbose_name="เบอร์โทร")
    email = models.EmailField(blank=True, verbose_name="อีเมล")
    line_user_id = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="LINE User ID",
        help_text="Phase 2: filled when customer links LINE account",
    )
    # Corporate fields
    is_corporate = models.BooleanField(default=False, verbose_name="นิติบุคคล")
    tax_id = models.CharField(
        max_length=13,
        blank=True,
        verbose_name="เลขประจำตัวผู้เสียภาษี",
        help_text="13 หลัก สำหรับออกใบกำกับภาษี",
    )
    billing_address = models.TextField(blank=True, verbose_name="ที่อยู่สำหรับออกใบกำกับ")
    # Internal notes
    notes = models.TextField(blank=True, verbose_name="หมายเหตุ")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "ลูกค้า"
        verbose_name_plural = "ลูกค้า"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["phone"]),
            models.Index(fields=["tax_id"]),
        ]

    def __str__(self):
        return self.name

    @property
    def outstanding_balance(self):
        """Sum of unpaid job balances for this customer."""
        from jobs.models import Job

        return (
            Job.objects.filter(customer=self, status__in=["ready", "completed"])
            .exclude(payment_status="paid")
            .aggregate(total=models.Sum("balance_due"))["total"]
            or 0
        )
