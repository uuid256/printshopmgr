"""Tests for Thai locale template filters."""

import datetime

import pytest

from dashboard.templatetags.thai_filters import baht, baht_text, thai_date, thai_date_short


class TestThaiDate:
    def test_converts_to_buddhist_era(self):
        d = datetime.date(2025, 2, 26)
        result = thai_date(d)
        assert "2568" in result  # 2025 + 543 = 2568
        assert "กุมภาพันธ์" in result
        assert "26" in result

    def test_none_returns_empty_string(self):
        assert thai_date(None) == ""

    def test_datetime_is_handled(self):
        dt = datetime.datetime(2025, 1, 15, 10, 30)
        result = thai_date(dt)
        assert "2568" in result
        assert "มกราคม" in result


class TestThaiDateShort:
    def test_short_format(self):
        d = datetime.date(2025, 2, 26)
        result = thai_date_short(d)
        assert "ก.พ." in result
        assert "68" in result  # last 2 digits of 2568


class TestBahtFilter:
    def test_formats_with_symbol(self):
        assert baht(1500) == "฿1,500.00"

    def test_custom_format(self):
        assert baht(1500, "฿{:,.0f}") == "฿1,500"


class TestBahtText:
    def test_zero(self):
        assert baht_text(0) == "ศูนย์บาทถ้วน"

    def test_one_hundred(self):
        assert baht_text(100) == "หนึ่งร้อยบาทถ้วน"

    def test_one_thousand(self):
        result = baht_text(1000)
        assert "พัน" in result
        assert "ถ้วน" in result

    def test_twelve_thousand_five_hundred(self):
        result = baht_text(12500)
        assert "หมื่น" in result
        assert "สอง" in result

    def test_with_satang(self):
        result = baht_text(100.50)
        assert "ห้าสิบสตางค์" in result
