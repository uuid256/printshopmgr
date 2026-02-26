"""
RBAC mixins and decorators for view-level access control.

Usage in views:
    class MyView(RoleRequiredMixin, View):
        required_roles = [Role.OWNER, Role.COUNTER]

Usage as decorator:
    @role_required(Role.OWNER)
    def my_view(request):
        ...
"""

from functools import wraps

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied

from .models import Role


class RoleRequiredMixin(LoginRequiredMixin):
    """
    Mixin that enforces role-based access on class-based views.

    Set `required_roles` as a list of Role values on the view class.
    Owners always pass (they have full access).
    """

    required_roles: list[str] = []

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not self._user_has_access(request.user):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def _user_has_access(self, user):
        if user.is_superuser or user.role == Role.OWNER:
            return True
        return not self.required_roles or user.role in self.required_roles


def role_required(*roles):
    """
    Decorator for function-based views.

    @role_required(Role.COUNTER, Role.OWNER)
    def my_view(request): ...
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                from django.conf import settings
                from django.shortcuts import redirect

                return redirect(settings.LOGIN_URL)
            if request.user.is_superuser or request.user.role == Role.OWNER:
                return view_func(request, *args, **kwargs)
            if roles and request.user.role not in roles:
                raise PermissionDenied
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator
