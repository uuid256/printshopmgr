"""
Document models — Thai tax-compliant invoices and receipts.

CRITICAL: Sequential document numbering uses SELECT FOR UPDATE to prevent
gaps in the sequence (required by Thai tax law).
Document numbers format: TX-YYYY-NNNNN (e.g., TX-2025-00001)
"""

from django.conf import settings
from django.db import models, transaction
from django.utils import timezone


class DocumentType(models.TextChoices):
    QUOTATION = "quotation", "ใบเสนอราคา"
    TAX_INVOICE = "tax_invoice", "ใบกำกับภาษี"
    RECEIPT = "receipt", "ใบเสร็จรับเงิน"
    CREDIT_NOTE = "credit_note", "ใบลดหนี้"


class Document(models.Model):
    """
    A financial document (quotation, invoice, receipt).

    document_number is assigned atomically using DB-level locking
    to guarantee sequential, gap-free numbering.
    """

    job = models.ForeignKey(
        "jobs.Job",
        on_delete=models.PROTECT,
        related_name="documents",
        verbose_name="งาน",
    )
    document_type = models.CharField(
        max_length=20,
        choices=DocumentType.choices,
        verbose_name="ประเภทเอกสาร",
    )
    document_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="เลขที่เอกสาร",
        help_text="ออกอัตโนมัติ เช่น TX-2025-00001",
    )
    sequence = models.PositiveIntegerField(verbose_name="ลำดับ")
    year = models.PositiveSmallIntegerField(verbose_name="ปี พ.ศ./ค.ศ.")

    # Snapshot of customer data at time of issue (immutable after creation)
    customer_name = models.CharField(max_length=200, verbose_name="ชื่อลูกค้า")
    customer_address = models.TextField(blank=True, verbose_name="ที่อยู่")
    customer_tax_id = models.CharField(max_length=13, blank=True, verbose_name="เลขผู้เสียภาษี")

    # Amounts
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="ยอดก่อนภาษี")
    vat_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=7, verbose_name="อัตรา VAT (%)"
    )
    vat_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="VAT")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="ยอดรวม")

    issued_at = models.DateTimeField(auto_now_add=True, verbose_name="วันที่ออก")
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name="ออกโดย",
    )
    notes = models.TextField(blank=True, verbose_name="หมายเหตุ")
    is_void = models.BooleanField(default=False, verbose_name="ยกเลิก")

    class Meta:
        verbose_name = "เอกสาร"
        verbose_name_plural = "เอกสาร"
        ordering = ["-issued_at"]
        indexes = [
            models.Index(fields=["document_type", "year", "sequence"]),
            models.Index(fields=["job"]),
        ]

    def __str__(self):
        return f"{self.document_number} — {self.get_document_type_display()}"

    def save(self, *args, **kwargs):
        if not self.pk:
            # New document — assign sequential number inside a transaction
            self._assign_document_number()
        super().save(*args, **kwargs)

    def _assign_document_number(self):
        """
        Assign the next sequential document number atomically.

        Uses SELECT FOR UPDATE to prevent race conditions between concurrent
        requests (required for Thai tax compliance — no gaps allowed).
        """
        current_year = timezone.now().year

        with transaction.atomic():
            last = (
                Document.objects.select_for_update()
                .filter(document_type=self.document_type, year=current_year)
                .order_by("-sequence")
                .first()
            )
            self.sequence = (last.sequence + 1) if last else 1
            self.year = current_year
            # Prefix per document type to keep sequences independent
            # QT-2026-00001, IV-2026-00001, RC-2026-00001, CN-2026-00001
            prefixes = {
                DocumentType.QUOTATION: "QT",
                DocumentType.TAX_INVOICE: "IV",
                DocumentType.RECEIPT: "RC",
                DocumentType.CREDIT_NOTE: "CN",
            }
            prefix = prefixes.get(self.document_type, "TX")
            self.document_number = f"{prefix}-{current_year}-{self.sequence:05d}"


class DocumentItem(models.Model):
    """Line items on a document."""

    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="items")
    description = models.CharField(max_length=255, verbose_name="รายการ")
    quantity = models.DecimalField(max_digits=10, decimal_places=3, verbose_name="จำนวน")
    unit = models.CharField(max_length=30, default="ชิ้น", verbose_name="หน่วย")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="ราคา/หน่วย")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="ยอด")

    class Meta:
        verbose_name = "รายการสินค้า"
        verbose_name_plural = "รายการสินค้า"
        ordering = ["id"]

    def save(self, *args, **kwargs):
        self.amount = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.description} × {self.quantity}"


class Setting(models.Model):
    """
    Key-value store for shop configuration.

    Examples: shop_name, shop_address, tax_id, promptpay_id, vat_included
    """

    key = models.CharField(max_length=100, unique=True, verbose_name="คีย์")
    value = models.TextField(verbose_name="ค่า")
    description = models.CharField(max_length=255, blank=True, verbose_name="คำอธิบาย")

    class Meta:
        app_label = "documents"
        verbose_name = "ตั้งค่าระบบ"
        verbose_name_plural = "ตั้งค่าระบบ"

    def __str__(self):
        return f"{self.key} = {self.value[:50]}"

    @classmethod
    def get(cls, key, default=""):
        try:
            return cls.objects.get(key=key).value
        except cls.DoesNotExist:
            return default
