"""
Custom User model with role-based access control.

Roles are stored as a CharField with choices so they are easy to check
without extra DB queries. A user can have only one primary role — this
keeps permission checks simple and predictable. If a staff member genuinely
needs two roles (e.g., owner who also does counter work), give them the
higher-privilege role.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.TextChoices):
    OWNER = "owner", "เจ้าของ (Owner)"
    COUNTER = "counter_staff", "พนักงานเคาน์เตอร์"
    DESIGNER = "designer", "นักออกแบบ"
    OPERATOR = "operator", "พนักงานผลิต"
    ACCOUNTANT = "accountant", "นักบัญชี"


class User(AbstractUser):
    """Extended user with a single primary role for RBAC."""

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.COUNTER,
        verbose_name="บทบาท",
    )
    phone = models.CharField(max_length=20, blank=True, verbose_name="เบอร์โทร")
    line_user_id = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="LINE User ID",
        help_text="For Phase 2 LINE notifications",
    )

    class Meta:
        verbose_name = "ผู้ใช้งาน"
        verbose_name_plural = "ผู้ใช้งาน"

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    # Convenience properties — use in templates and views
    @property
    def is_owner(self):
        return self.role == Role.OWNER

    @property
    def is_counter(self):
        return self.role == Role.COUNTER

    @property
    def is_designer(self):
        return self.role == Role.DESIGNER

    @property
    def is_operator(self):
        return self.role == Role.OPERATOR

    @property
    def is_accountant(self):
        return self.role == Role.ACCOUNTANT

    def has_any_role(self, *roles):
        """Check if user has one of the given roles."""
        return self.role in roles
