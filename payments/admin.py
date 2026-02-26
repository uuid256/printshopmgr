from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import BankAccount, Payment


@admin.register(BankAccount)
class BankAccountAdmin(ModelAdmin):
    list_display = ("bank_name", "account_name", "account_number", "promptpay_id", "is_active", "sort_order")
    list_editable = ("is_active", "sort_order")


@admin.register(Payment)
class PaymentAdmin(ModelAdmin):
    list_display = ("job", "amount", "method", "is_deposit", "received_by", "received_at")
    list_filter = ("method", "is_deposit")
    search_fields = ("job__title", "reference_number")
    readonly_fields = ("received_at",)
    date_hierarchy = "received_at"
