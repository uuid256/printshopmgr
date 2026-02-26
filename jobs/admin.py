from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .models import Job, JobApproval, JobFile, JobStatusHistory


class JobStatusHistoryInline(TabularInline):
    model = JobStatusHistory
    extra = 0
    readonly_fields = ("from_status", "to_status", "changed_by", "note", "changed_at")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class JobFileInline(TabularInline):
    model = JobFile
    extra = 0
    readonly_fields = ("uploaded_at", "uploaded_by")


@admin.register(Job)
class JobAdmin(ModelAdmin):
    list_display = (
        "id", "title", "customer", "product_type", "status",
        "payment_status", "quoted_price", "balance_due", "due_date", "created_at",
    )
    list_filter = ("status", "payment_status", "product_type")
    search_fields = ("title", "customer__name", "customer__phone")
    readonly_fields = ("tracking_token", "created_at", "updated_at", "total_paid", "balance_due")
    date_hierarchy = "created_at"
    inlines = [JobFileInline, JobStatusHistoryInline]

    @admin.display(description="ยอดค้างชำระ")
    def balance_due(self, obj):
        return f"฿{obj.balance_due:,.2f}"


@admin.register(JobStatusHistory)
class JobStatusHistoryAdmin(ModelAdmin):
    list_display = ("job", "from_status", "to_status", "changed_by", "changed_at")
    readonly_fields = ("job", "from_status", "to_status", "changed_by", "note", "changed_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
