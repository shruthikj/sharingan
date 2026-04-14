"""Generate valid and invalid test data for form fields."""

from __future__ import annotations

import random
import string
from typing import Any

from sharingan.data.fields import FieldType

# Realistic sample data — static to keep tests deterministic
_SAMPLE_FIRST_NAMES = ["Alice", "Bob", "Carol", "David", "Eve"]
_SAMPLE_LAST_NAMES = ["Smith", "Johnson", "Chen", "Patel", "Kim"]
_SAMPLE_DOMAINS = ["example.com", "example.org", "test.local"]


def generate_valid_data(field_type: FieldType, seed: int = 42) -> Any:
    """Generate realistic, valid test data for a field type.

    Args:
        field_type: The semantic type of the field.
        seed: Random seed for deterministic output.

    Returns:
        A valid value for the field.
    """
    rng = random.Random(seed)

    if field_type == FieldType.EMAIL:
        return f"sharingan-test-{rng.randint(1000, 9999)}@{rng.choice(_SAMPLE_DOMAINS)}"

    if field_type == FieldType.PASSWORD or field_type == FieldType.CONFIRM_PASSWORD:
        return "SharinganT3st!2026"

    if field_type == FieldType.USERNAME:
        return f"sharingan_user_{rng.randint(100, 999)}"

    if field_type == FieldType.NAME:
        first = rng.choice(_SAMPLE_FIRST_NAMES)
        last = rng.choice(_SAMPLE_LAST_NAMES)
        return f"{first} {last}"

    if field_type == FieldType.PHONE:
        return "+15555550100"  # Reserved US test number

    if field_type == FieldType.URL:
        return "https://example.com"

    if field_type == FieldType.NUMBER:
        return 42

    if field_type == FieldType.DATE:
        return "2025-06-15"

    if field_type == FieldType.TEXTAREA:
        return "This is a sample text for testing purposes. It contains multiple words and basic punctuation."

    if field_type == FieldType.CHECKBOX:
        return True

    return "Test Value"


def generate_invalid_data(field_type: FieldType) -> list[dict[str, Any]]:
    """Generate invalid test cases for a field type.

    Each invalid case includes the bad value and what validation error
    it should trigger (for assertion purposes).

    Args:
        field_type: The semantic type of the field.

    Returns:
        List of dicts with "value" and "expected_error_pattern" keys.
    """
    if field_type == FieldType.EMAIL:
        return [
            {"value": "", "expected_error_pattern": r"required|empty"},
            {"value": "notanemail", "expected_error_pattern": r"invalid|valid email"},
            {"value": "@example.com", "expected_error_pattern": r"invalid|valid email"},
            {"value": "user@", "expected_error_pattern": r"invalid|valid email"},
            {"value": "user@.com", "expected_error_pattern": r"invalid|valid email"},
            {"value": "a" * 300 + "@example.com", "expected_error_pattern": r"long|max|length"},
        ]

    if field_type == FieldType.PASSWORD:
        return [
            {"value": "", "expected_error_pattern": r"required|empty"},
            {"value": "123", "expected_error_pattern": r"short|length|at least|minimum"},
            {"value": "password", "expected_error_pattern": r"weak|common|requirements"},
            {"value": "abc", "expected_error_pattern": r"short|length|at least"},
        ]

    if field_type == FieldType.CONFIRM_PASSWORD:
        return [
            {"value": "DifferentPassword123!", "expected_error_pattern": r"match|same"},
        ]

    if field_type == FieldType.USERNAME:
        return [
            {"value": "", "expected_error_pattern": r"required|empty"},
            {"value": "a", "expected_error_pattern": r"short|length|at least"},
            {"value": "user with spaces", "expected_error_pattern": r"invalid|spaces|characters"},
            {"value": "a" * 200, "expected_error_pattern": r"long|max|length"},
        ]

    if field_type == FieldType.PHONE:
        return [
            {"value": "", "expected_error_pattern": r"required|empty"},
            {"value": "notaphone", "expected_error_pattern": r"invalid|valid phone"},
            {"value": "123", "expected_error_pattern": r"invalid|short|valid"},
        ]

    if field_type == FieldType.URL:
        return [
            {"value": "", "expected_error_pattern": r"required|empty"},
            {"value": "notaurl", "expected_error_pattern": r"invalid|valid url"},
            {"value": "ftp://", "expected_error_pattern": r"invalid|http"},
        ]

    if field_type == FieldType.NUMBER:
        return [
            {"value": "notanumber", "expected_error_pattern": r"number|numeric|invalid"},
            {"value": "", "expected_error_pattern": r"required|empty"},
        ]

    if field_type == FieldType.DATE:
        return [
            {"value": "", "expected_error_pattern": r"required|empty"},
            {"value": "not a date", "expected_error_pattern": r"invalid|valid date"},
            {"value": "2099-13-45", "expected_error_pattern": r"invalid|valid date"},
        ]

    # Generic text field
    return [
        {"value": "", "expected_error_pattern": r"required|empty"},
        {"value": "x" * 10000, "expected_error_pattern": r"long|max|length"},
    ]


def generate_edge_cases(field_type: FieldType) -> list[str]:
    """Generate edge case values for robustness testing.

    These are values that should NOT break the application (but might).
    Unlike invalid data, these may be accepted — we're testing that the
    app handles them without crashing.

    Args:
        field_type: The field type.

    Returns:
        List of edge case values.
    """
    universal = [
        "' OR '1'='1",  # SQL injection attempt
        "<script>alert('xss')</script>",  # XSS attempt
        "   leading and trailing spaces   ",
        "unicode: 你好 مرحبا 🎉",
        "\n\t\r\0",  # Control characters
    ]

    if field_type == FieldType.EMAIL:
        return [
            "test+tag@example.com",  # Plus addressing
            "test.with.dots@example.com",
            "TEST@EXAMPLE.COM",  # Case handling
        ]

    if field_type == FieldType.PASSWORD:
        return [
            "P@ssw0rd with spaces!",
            "🔒SecurePass123!🔑",  # Emoji
            "a" * 100,  # Very long
        ]

    return universal
