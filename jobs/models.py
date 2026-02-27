"""
Job models — the core of the print shop workflow.

A Job moves through a defined status workflow with every transition
recorded in JobStatusHistory for full audit trail.
"""

import os
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class JobStatus(models.TextChoices):
    # Counter intake
    PENDING = "pending", "รอดำเนินการ"
    # Design workflow
    DESIGNING = "designing", "กำลังออกแบบ"
    AWAITING_APPROVAL = "awaiting_approval", "รอลูกค้าอนุมัติ"
    REVISION = "revision", "แก้ไขงาน"
    APPROVED = "approved", "อนุมัติแล้ว"
    # Production
    PRINTING = "printing", "กำลังพิมพ์"
    CUTTING = "cutting", "กำลังตัด"
    LAMINATING = "laminating", "กำลังเคลือบ"
    # Completion
    READY = "ready", "พร้อมรับ"
    COMPLETED = "completed", "เสร็จสิ้น"
    # Special
    CANCELLED = "cancelled", "ยกเลิก"
    ON_HOLD = "on_hold", "พักงาน"


# Valid status transitions — enforced in transition_to()
ALLOWED_TRANSITIONS = {
    JobStatus.PENDING: {JobStatus.DESIGNING, JobStatus.PRINTING, JobStatus.ON_HOLD, JobStatus.CANCELLED},
    JobStatus.DESIGNING: {JobStatus.AWAITING_APPROVAL, JobStatus.REVISION, JobStatus.ON_HOLD},
    JobStatus.AWAITING_APPROVAL: {JobStatus.APPROVED, JobStatus.REVISION},
    JobStatus.REVISION: {JobStatus.AWAITING_APPROVAL, JobStatus.ON_HOLD},
    JobStatus.APPROVED: {JobStatus.PRINTING, JobStatus.ON_HOLD},
    JobStatus.PRINTING: {JobStatus.CUTTING, JobStatus.LAMINATING, JobStatus.READY},
    JobStatus.CUTTING: {JobStatus.LAMINATING, JobStatus.READY},
    JobStatus.LAMINATING: {JobStatus.READY},
    JobStatus.READY: {JobStatus.COMPLETED},
    JobStatus.COMPLETED: set(),
    JobStatus.CANCELLED: set(),
    JobStatus.ON_HOLD: {JobStatus.PENDING, JobStatus.DESIGNING, JobStatus.PRINTING},
}


class PaymentStatus(models.TextChoices):
    UNPAID = "unpaid", "ยังไม่ชำระ"
    PARTIAL = "partial", "ชำระบางส่วน"
    PAID = "paid", "ชำระครบ"


def job_file_upload_path(instance, filename):
    now = timezone.now()
    return f"jobs/{now.year}/{now.month:02d}/job_{instance.job_id}/{filename}"


class Job(models.Model):
    """Central job record — one customer order = one job."""

    # Relationships
    customer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.PROTECT,
        related_name="jobs",
        verbose_name="ลูกค้า",
    )
    product_type = models.ForeignKey(
        "production.ProductType",
        on_delete=models.PROTECT,
        verbose_name="ประเภทสินค้า",
    )
    assigned_designer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="design_jobs",
        verbose_name="นักออกแบบ",
    )

    # Job details
    title = models.CharField(max_length=200, verbose_name="ชื่องาน")
    description = models.TextField(blank=True, verbose_name="รายละเอียด")
    quantity = models.PositiveIntegerField(default=1, verbose_name="จำนวน")
    width_cm = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="กว้าง (ซม.)"
    )
    height_cm = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="สูง (ซม.)"
    )

    # Pricing
    quoted_price = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="ราคาที่เสนอ"
    )
    deposit_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="มัดจำ"
    )
    discount_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="ส่วนลด"
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=JobStatus.choices,
        default=JobStatus.PENDING,
        verbose_name="สถานะ",
        db_index=True,
    )
    payment_status = models.CharField(
        max_length=10,
        choices=PaymentStatus.choices,
        default=PaymentStatus.UNPAID,
        verbose_name="สถานะการชำระ",
    )

    # Dates
    due_date = models.DateField(null=True, blank=True, verbose_name="กำหนดส่ง")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_jobs",
        verbose_name="ผู้รับงาน",
    )

    # Public tracking token (no-login customer tracking page)
    tracking_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    # Internal notes
    internal_notes = models.TextField(blank=True, verbose_name="หมายเหตุภายใน")

    class Meta:
        verbose_name = "งาน"
        verbose_name_plural = "งาน"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["customer", "status"]),
            models.Index(fields=["tracking_token"]),
        ]

    def __str__(self):
        return f"#{self.pk} {self.title} — {self.customer.name}"

    @property
    def total_paid(self):
        return self.payments.aggregate(total=models.Sum("amount"))["total"] or 0

    @property
    def balance_due(self):
        return self.quoted_price - self.discount_amount - self.total_paid

    def transition_to(self, new_status, changed_by=None, note=""):
        """
        Move job to new_status, enforcing allowed transitions.
        Records history entry for every change.
        changed_by=None is allowed for customer-initiated transitions (public tracking page).
        """
        allowed = ALLOWED_TRANSITIONS.get(self.status, set())
        if new_status not in allowed:
            raise ValueError(
                f"Cannot transition from '{self.status}' to '{new_status}'. "
                f"Allowed: {allowed}"
            )
        old_status = self.status
        self.status = new_status
        self.save(update_fields=["status", "updated_at"])

        JobStatusHistory.objects.create(
            job=self,
            from_status=old_status,
            to_status=new_status,
            changed_by=changed_by,
            note=note,
        )

    def get_tracking_url(self):
        from django.urls import reverse

        return reverse("public:track", kwargs={"token": self.tracking_token})

    def first_proof_image(self):
        """Return the first proof file that is an image (uses prefetch cache)."""
        for f in self.files.all():
            if f.file_type == JobFile.FileType.PROOF and f.is_image:
                return f
        return None


class JobStatusHistory(models.Model):
    """Immutable audit log of every status change on a job."""

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="status_history")
    from_status = models.CharField(max_length=20, choices=JobStatus.choices)
    to_status = models.CharField(max_length=20, choices=JobStatus.choices)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="เปลี่ยนโดย",
    )
    note = models.TextField(blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "ประวัติสถานะ"
        verbose_name_plural = "ประวัติสถานะ"
        ordering = ["-changed_at"]

    def __str__(self):
        return f"Job #{self.job_id}: {self.from_status} → {self.to_status}"


class JobFile(models.Model):
    """Files attached to a job: customer artwork, design proofs, references."""

    class FileType(models.TextChoices):
        ARTWORK = "artwork", "ไฟล์งานลูกค้า"
        PROOF = "proof", "ไฟล์ proof"
        REFERENCE = "reference", "ไฟล์อ้างอิง"
        OUTPUT = "output", "ไฟล์ผลงาน"

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="files")
    file = models.FileField(upload_to=job_file_upload_path, verbose_name="ไฟล์")
    file_type = models.CharField(max_length=15, choices=FileType.choices, default=FileType.ARTWORK)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "ไฟล์งาน"
        verbose_name_plural = "ไฟล์งาน"
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.get_file_type_display()} — Job #{self.job_id}"

    @property
    def filename(self):
        return os.path.basename(self.file.name)

    @property
    def is_image(self):
        ext = os.path.splitext(self.file.name)[1].lower()
        return ext in {".jpg", ".jpeg", ".png", ".gif", ".webp"}

    @property
    def filesize_display(self):
        try:
            size = self.file.size
            if size < 1024:
                return f"{size} B"
            elif size < 1024 * 1024:
                return f"{size // 1024} KB"
            else:
                return f"{size / (1024 * 1024):.1f} MB"
        except (FileNotFoundError, OSError):
            return ""


class JobApproval(models.Model):
    """
    Design approval record from customer.

    Phase 1: manual approval logged by counter staff.
    Phase 2: customer clicks approve via public URL or LINE message.
    """

    class Decision(models.TextChoices):
        APPROVED = "approved", "อนุมัติ"
        REVISION = "revision", "ขอแก้ไข"

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="approvals")
    proof_file = models.ForeignKey(
        JobFile,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="ไฟล์ proof ที่ส่งให้",
    )
    decision = models.CharField(max_length=10, choices=Decision.choices)
    revision_notes = models.TextField(blank=True, verbose_name="หมายเหตุการแก้ไข")
    decided_at = models.DateTimeField(auto_now_add=True)
    decided_by_customer = models.BooleanField(
        default=False,
        help_text="True if customer approved directly (Phase 2); False if staff recorded",
    )
    approved_by_name = models.CharField(max_length=100, blank=True, verbose_name="ชื่อลูกค้า")
    approved_by_ip = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP ลูกค้า")

    class Meta:
        verbose_name = "การอนุมัติ"
        verbose_name_plural = "การอนุมัติ"
        ordering = ["-decided_at"]

    def __str__(self):
        return f"Job #{self.job_id} — {self.get_decision_display()}"
