from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from unfold.admin import ModelAdmin

from .models import User


@admin.register(User)
class UserAdmin(ModelAdmin, BaseUserAdmin):
    list_display = ("username", "get_full_name", "email", "role", "is_active", "date_joined")
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("username", "first_name", "last_name", "email")
    ordering = ("-date_joined",)

    fieldsets = BaseUserAdmin.fieldsets + (
        (
            "บทบาทและข้อมูลเพิ่มเติม",
            {"fields": ("role", "phone", "line_user_id")},
        ),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (
            "บทบาทและข้อมูลเพิ่มเติม",
            {"fields": ("role", "phone")},
        ),
    )
