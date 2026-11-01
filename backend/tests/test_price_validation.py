"""Automated tests for decimal price validation, floating-point safety, and Algerian inputs."""

from decimal import Decimal
import pytest
from pydantic import ValidationError
from app.schemas.customer import CustomerCreate
from app.schemas.product import ProductCreate


def test_valid_product_decimal_prices():
    """Verify standard positive prices in Algerian Dinars are accepted and normalized."""
    prod = ProductCreate(
        sku="SCR-IPH-12-OLED",
        name="iPhone 12 OLED Display",
        category_id=1,
        selling_price=Decimal("18500.50"),
        available_quantity=10,
    )
    assert prod.selling_price == Decimal("18500.50")

    # Free or zero price item (e.g. warranty / promotional spare)
    prod_zero = ProductCreate(
        sku="PRM-SAM-TOOL-KIT",
        name="Repair Tool Opening Pick",
        category_id=1,
        selling_price=Decimal("0.00"),
    )
    assert prod_zero.selling_price == Decimal("0.00")


def test_negative_product_price_rejected():
    """Ensure negative product selling price is strictly rejected."""
    with pytest.raises(ValidationError, match="greater than or equal to 0"):
        ProductCreate(
            sku="SCR-NEG-PRICE",
            name="Negative Price Screen",
            category_id=1,
            selling_price=Decimal("-500.00"),
        )


def test_excessive_decimal_places_rejected():
    """Ensure sub-cent fractions (>2 decimal places) are rejected to prevent financial rounding bugs."""
    with pytest.raises(ValidationError, match="decimal places"):
        ProductCreate(
            sku="SCR-INVALID-DEC",
            name="Fractional Price Screen",
            category_id=1,
            selling_price=Decimal("1500.999"),
        )


def test_floating_point_arithmetic_safety():
    """Demonstrate that exact Decimal handling avoids float precision issues."""
    # Standard Python floats exhibit rounding errors (e.g. 0.1 + 0.2 = 0.30000000000000004)
    # With Decimal, precision is exact
    p1 = Decimal("14500.10")
    p2 = Decimal("14500.20")
    total = p1 + p2
    assert total == Decimal("29000.30")
    assert str(total) == "29000.30"


def test_sku_validation_rules():
    """Ensure SKU formats are validated and uppercase-normalized."""
    prod = ProductCreate(
        sku="  bat-sam-s20  ",
        name="Samsung Galaxy S20 Battery",
        category_id=2,
        selling_price=Decimal("4500.00"),
    )
    assert prod.sku == "BAT-SAM-S20"

    # Reject invalid characters
    with pytest.raises(ValidationError, match="SKU must only contain alphanumeric characters"):
        ProductCreate(
            sku="BAT#SAM@S20!?",
            name="Samsung Galaxy S20 Battery",
            category_id=2,
            selling_price=Decimal("4500.00"),
        )


def test_algerian_phone_number_validation():
    """Ensure customer phone number validation matches standard Algerian formats (05/06/07/213)."""
    # Standard 05/06/07
    c1 = CustomerCreate(full_name="Walid", phone_number="0550123456")
    assert c1.phone_number == "0550123456"

    # +213 country code format normalized to standard national format
    c2 = CustomerCreate(full_name="Farid", phone_number="+213 661 12 34 56")
    assert c2.phone_number == "0661123456"

    # 07 format
    c3 = CustomerCreate(full_name="Karim", phone_number="0770-99-88-77")
    assert c3.phone_number == "0770998877"

    # Invalid phone numbers rejected
    with pytest.raises(ValidationError, match="Invalid Algerian phone number"):
        CustomerCreate(full_name="Invalid", phone_number="0123456789")

    with pytest.raises(ValidationError, match="Invalid Algerian phone number"):
        CustomerCreate(full_name="TooShort", phone_number="0550123")
