"""Tests for Job model — especially status transitions."""

import pytest

from jobs.models import Job, JobStatus


@pytest.mark.django_db
class TestJobStatusTransitions:
    def test_valid_transition_pending_to_designing(self, job, counter_user):
        job.transition_to(JobStatus.DESIGNING, changed_by=counter_user)
        assert job.status == JobStatus.DESIGNING

    def test_valid_transition_records_history(self, job, counter_user):
        job.transition_to(JobStatus.DESIGNING, changed_by=counter_user, note="เริ่มออกแบบ")
        history = job.status_history.first()
        assert history.from_status == JobStatus.PENDING
        assert history.to_status == JobStatus.DESIGNING
        assert history.note == "เริ่มออกแบบ"
        assert history.changed_by == counter_user

    def test_invalid_transition_raises_value_error(self, job, counter_user):
        with pytest.raises(ValueError, match="Cannot transition"):
            job.transition_to(JobStatus.COMPLETED, changed_by=counter_user)

    def test_balance_due_calculation(self, job):
        assert job.balance_due == job.quoted_price

    def test_balance_due_after_payment(self, db, job, counter_user):
        from payments.models import Payment, PaymentMethod

        Payment.objects.create(
            job=job,
            amount=100,
            method=PaymentMethod.CASH,
            received_by=counter_user,
        )
        job.refresh_from_db()
        assert job.balance_due == job.quoted_price - 100

    def test_tracking_token_unique(self, db, customer, product_type, counter_user):
        job1 = Job.objects.create(
            customer=customer, product_type=product_type,
            title="งาน 1", quantity=1, quoted_price=100, created_by=counter_user
        )
        job2 = Job.objects.create(
            customer=customer, product_type=product_type,
            title="งาน 2", quantity=1, quoted_price=100, created_by=counter_user
        )
        assert job1.tracking_token != job2.tracking_token
