"""
Production reference models.

ProductType and Material are configured via Django Admin by the owner.
MaterialUsage tracks what materials were consumed per job.
"""

from django.db import models


class ProductType(models.Model):
    """
    Category of print product: Banner, Sticker, Business Card, etc.

    Each product type has a base pricing structure that the auto-pricing
    engine uses as a starting point.
    """

    name = models.CharField(max_length=100, verbose_name="ประเภทสินค้า")
    name_en = models.CharField(max_length=100, blank=True, verbose_name="ชื่อภาษาอังกฤษ")
    unit = models.CharField(
        max_length=30,
        default="ชิ้น",
        verbose_name="หน่วย",
        help_text="e.g. ชิ้น, ตร.ม., เมตร",
    )
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="ราคาฐาน",
    )
    # Pricing formula: flat, per_sqm, per_unit
    pricing_method = models.CharField(
        max_length=20,
        choices=[
            ("flat", "ราคาคงที่"),
            ("per_sqm", "ต่อตารางเมตร"),
            ("per_unit", "ต่อชิ้น"),
        ],
        default="per_unit",
        verbose_name="วิธีคิดราคา",
    )
    requires_design = models.BooleanField(
        default=True,
        verbose_name="ต้องผ่านขั้นตอนออกแบบ",
    )
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = "ประเภทสินค้า"
        verbose_name_plural = "ประเภทสินค้า"
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name


class Material(models.Model):
    """
    Raw material inventory: vinyl, paper, ink, etc.

    MaterialUsage links to Job to track consumption.
    Low-stock alerts (Phase 4) use the min_quantity threshold.
    """

    name = models.CharField(max_length=150, verbose_name="ชื่อวัสดุ")
    unit = models.CharField(max_length=20, verbose_name="หน่วย", help_text="e.g. ม้วน, แผ่น, กก.")
    cost_per_unit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="ต้นทุน/หน่วย (บาท)",
    )
    quantity_in_stock = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=0,
        verbose_name="คงเหลือ",
    )
    min_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=0,
        verbose_name="ขั้นต่ำก่อนแจ้งเตือน",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "วัสดุ"
        verbose_name_plural = "วัสดุ"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.quantity_in_stock} {self.unit})"

    @property
    def is_low_stock(self):
        return self.quantity_in_stock <= self.min_quantity


class MaterialUsage(models.Model):
    """Records material consumed by a job."""

    job = models.ForeignKey(
        "jobs.Job",
        on_delete=models.CASCADE,
        related_name="material_usages",
        verbose_name="งาน",
    )
    material = models.ForeignKey(
        Material,
        on_delete=models.PROTECT,
        verbose_name="วัสดุ",
    )
    quantity_used = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        verbose_name="จำนวนที่ใช้",
    )
    recorded_at = models.DateTimeField(auto_now_add=True)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "การใช้วัสดุ"
        verbose_name_plural = "การใช้วัสดุ"

    def __str__(self):
        return f"{self.material.name} × {self.quantity_used}"
