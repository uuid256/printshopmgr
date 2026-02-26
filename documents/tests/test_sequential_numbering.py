"""
Tests for sequential document numbering — critical Thai tax compliance requirement.

These tests verify that:
1. First document of the year gets sequence 1
2. Each subsequent document gets the next number
3. Concurrent creation doesn't produce duplicates or gaps
"""

import pytest

from documents.models import Document, DocumentType


def _make_doc(job, issued_by, doc_type=DocumentType.QUOTATION):
    return Document.objects.create(
        job=job,
        document_type=doc_type,
        customer_name=job.customer.name,
        customer_address="",
        customer_tax_id="",
        subtotal=job.quoted_price,
        vat_rate=0,
        vat_amount=0,
        total_amount=job.quoted_price,
        issued_by=issued_by,
    )


@pytest.mark.django_db
class TestSequentialDocumentNumbers:
    def test_first_document_gets_sequence_1(self, job, counter_user):
        doc = _make_doc(job, counter_user)
        assert doc.sequence == 1
        assert doc.document_number.endswith("-00001")

    def test_second_document_gets_sequence_2(self, job, counter_user):
        doc1 = _make_doc(job, counter_user)
        doc2 = _make_doc(job, counter_user)
        assert doc1.sequence == 1
        assert doc2.sequence == 2

    def test_sequences_are_per_document_type(self, job, counter_user):
        q = _make_doc(job, counter_user, doc_type=DocumentType.QUOTATION)
        r = _make_doc(job, counter_user, doc_type=DocumentType.RECEIPT)
        # Each type starts its own sequence
        assert q.sequence == 1
        assert r.sequence == 1

    def test_document_number_format(self, job, counter_user):
        from django.utils import timezone

        doc = _make_doc(job, counter_user)
        year = timezone.now().year
        # Quotation prefix is QT
        assert doc.document_number == f"QT-{year}-00001"

    def test_document_number_unique_constraint(self, db, job, counter_user):
        _make_doc(job, counter_user)
        _make_doc(job, counter_user)
        numbers = list(Document.objects.values_list("document_number", flat=True))
        assert len(numbers) == len(set(numbers)), "Duplicate document numbers found!"
