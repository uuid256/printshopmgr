"""Tests for accounts models and RBAC logic."""

import pytest
from django.contrib.auth import get_user_model

from accounts.models import Role

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    def test_user_str_includes_role_display(self):
        user = User(username="test", first_name="สมชาย", last_name="ใจดี", role=Role.DESIGNER)
        assert "นักออกแบบ" in str(user)

    def test_is_owner_property(self, owner_user):
        assert owner_user.is_owner is True
        assert owner_user.is_counter is False

    def test_is_counter_property(self, counter_user):
        assert counter_user.is_counter is True
        assert counter_user.is_owner is False

    def test_has_any_role_true(self, counter_user):
        assert counter_user.has_any_role(Role.COUNTER, Role.OWNER) is True

    def test_has_any_role_false(self, counter_user):
        assert counter_user.has_any_role(Role.OWNER, Role.ACCOUNTANT) is False

    def test_default_role_is_counter(self, db):
        user = User.objects.create_user(username="newuser", password="pass")
        assert user.role == Role.COUNTER
