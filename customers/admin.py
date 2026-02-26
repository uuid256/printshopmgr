from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Customer, CustomerType


@admin.register(CustomerType)
class CustomerTypeAdmin(ModelAdmin):
    list_display = ("name", "credit_days", "discount_percent", "is_active")
    list_filter = ("is_active",)


@admin.register(Customer)
class CustomerAdmin(ModelAdmin):
    list_display = ("name", "phone", "customer_type", "is_corporate", "is_active", "created_at")
    list_filter = ("customer_type", "is_corporate", "is_active")
    search_fields = ("name", "phone", "tax_id", "email")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("ข้อมูลพื้นฐาน", {"fields": ("customer_type", "name", "phone", "email")}),
        (
            "ข้อมูลนิติบุคคล",
            {
                "fields": ("is_corporate", "tax_id", "billing_address"),
                "classes": ["collapse"],
            },
        ),
        ("LINE & หมายเหตุ", {"fields": ("line_user_id", "notes"), "classes": ["collapse"]}),
        ("สถานะ", {"fields": ("is_active", "created_at", "updated_at")}),
    )
