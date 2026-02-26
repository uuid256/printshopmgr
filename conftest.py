"""
Pytest configuration and shared fixtures.
"""

import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def owner_user(db):
    from accounts.models import Role

    return User.objects.create_user(
        username="owner",
        password="testpass123",
        role=Role.OWNER,
        first_name="เจ้าของ",
        last_name="ทดสอบ",
    )


@pytest.fixture
def counter_user(db):
    from accounts.models import Role

    return User.objects.create_user(
        username="counter",
        password="testpass123",
        role=Role.COUNTER,
    )


@pytest.fixture
def designer_user(db):
    from accounts.models import Role

    return User.objects.create_user(
        username="designer",
        password="testpass123",
        role=Role.DESIGNER,
    )


@pytest.fixture
def customer_type(db):
    from customers.models import CustomerType

    return CustomerType.objects.create(name="ทั่วไป", credit_days=0, discount_percent=0)


@pytest.fixture
def customer(db, customer_type):
    from customers.models import Customer

    return Customer.objects.create(
        customer_type=customer_type,
        name="บริษัท ทดสอบ จำกัด",
        phone="0812345678",
    )


@pytest.fixture
def product_type(db):
    from production.models import ProductType

    return ProductType.objects.create(
        name="ป้ายไวนิล",
        unit="ตร.ม.",
        base_price=150,
        pricing_method="per_sqm",
    )


@pytest.fixture
def job(db, customer, product_type, counter_user):
    from jobs.models import Job

    return Job.objects.create(
        customer=customer,
        product_type=product_type,
        title="ป้ายงานเปิดร้าน",
        quantity=1,
        width_cm=200,
        height_cm=100,
        quoted_price=300,
        created_by=counter_user,
    )
