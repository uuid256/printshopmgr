"""
Thai locale template filters.

Usage in templates:
    {% load thai_filters %}
    {{ some_date|thai_date }}          → "26 กุมภาพันธ์ 2568"
    {{ some_date|thai_date_short }}    → "26 ก.พ. 68"
    {{ 12500|baht_text }}              → "หนึ่งหมื่นสองพันห้าร้อยบาทถ้วน"
    {{ 12500|baht:"฿{:,.0f}" }}       → "฿12,500"
"""

from django import template
from django.utils import timezone

register = template.Library()

THAI_MONTHS_FULL = [
    "", "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน",
    "พฤษภาคม", "มิถุนายน", "กรกฎาคม", "สิงหาคม",
    "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม",
]

THAI_MONTHS_SHORT = [
    "", "ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.",
    "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.",
    "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค.",
]

ONES = ["", "หนึ่ง", "สอง", "สาม", "สี่", "ห้า", "หก", "เจ็ด", "แปด", "เก้า"]
TENS = ["", "สิบ", "ยี่สิบ", "สามสิบ", "สี่สิบ", "ห้าสิบ", "หกสิบ", "เจ็ดสิบ", "แปดสิบ", "เก้าสิบ"]
PLACES = ["", "สิบ", "ร้อย", "พัน", "หมื่น", "แสน", "ล้าน"]


@register.filter
def thai_date(value):
    """Convert date/datetime to Thai Buddhist Era full date string."""
    if value is None:
        return ""
    if hasattr(value, "date"):
        value = value.date()
    try:
        be_year = value.year + 543
        return f"{value.day} {THAI_MONTHS_FULL[value.month]} {be_year}"
    except (AttributeError, IndexError):
        return str(value)


@register.filter
def thai_date_short(value):
    """Convert date to short Thai Buddhist Era format."""
    if value is None:
        return ""
    if hasattr(value, "date"):
        value = value.date()
    try:
        be_year = str(value.year + 543)[-2:]
        return f"{value.day} {THAI_MONTHS_SHORT[value.month]} {be_year}"
    except (AttributeError, IndexError):
        return str(value)


@register.filter
def baht(value, fmt="฿{:,.2f}"):
    """Format number as Thai baht with symbol."""
    try:
        return fmt.format(float(value))
    except (ValueError, TypeError):
        return value


@register.filter
def baht_text(value):
    """
    Convert a number to Thai baht words.

    Examples:
        100     → "หนึ่งร้อยบาทถ้วน"
        1500.50 → "หนึ่งพันห้าร้อยบาทห้าสิบสตางค์"
        0       → "ศูนย์บาทถ้วน"
    """
    try:
        value = float(value)
    except (ValueError, TypeError):
        return str(value)

    if value < 0:
        return "ลบ" + baht_text(-value)

    baht_part = int(value)
    satang_part = round((value - baht_part) * 100)

    result = _number_to_thai(baht_part) + "บาท"
    if satang_part > 0:
        result += _number_to_thai(satang_part) + "สตางค์"
    else:
        result += "ถ้วน"
    return result


def _number_to_thai(n):
    """Convert integer to Thai word string (up to 9,999,999)."""
    if n == 0:
        return "ศูนย์"

    result = ""
    if n >= 1_000_000:
        result += _number_to_thai(n // 1_000_000) + "ล้าน"
        n %= 1_000_000

    place_names = ["แสน", "หมื่น", "พัน", "ร้อย"]
    place_values = [100_000, 10_000, 1_000, 100]

    for name, pv in zip(place_names, place_values):
        if n >= pv:
            digit = n // pv
            # Special case: สิบเอ็ด (11) not สิบหนึ่ง
            word = ONES[digit] if digit != 1 or pv != 10 else ""
            result += word + name
            n %= pv

    if n >= 10:
        tens_digit = n // 10
        if tens_digit == 2:
            result += "ยี่สิบ"
        elif tens_digit == 1:
            result += "สิบ"
        else:
            result += ONES[tens_digit] + "สิบ"
        n %= 10

    if n > 0:
        # "เอ็ด" instead of "หนึ่ง" when it's the last digit and > 11
        if n == 1 and result and not result.endswith("สิบ"):
            result += "เอ็ด"
        else:
            result += ONES[n]

    return result
