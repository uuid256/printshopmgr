from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .models import Document, DocumentItem, Setting


class DocumentItemInline(TabularInline):
    model = DocumentItem
    extra = 0


@admin.register(Document)
class DocumentAdmin(ModelAdmin):
    list_display = (
        "document_number", "document_type", "customer_name", "total_amount", "issued_at", "is_void"
    )
    list_filter = ("document_type", "is_void", "year")
    search_fields = ("document_number", "customer_name", "customer_tax_id")
    readonly_fields = ("document_number", "sequence", "year", "issued_at")
    date_hierarchy = "issued_at"
    inlines = [DocumentItemInline]

    def has_delete_permission(self, request, obj=None):
        # Documents should be voided, never deleted
        return False


@admin.register(Setting)
class SettingAdmin(ModelAdmin):
    list_display = ("key", "value", "description")
    search_fields = ("key", "description")
