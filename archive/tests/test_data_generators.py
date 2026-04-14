"""Tests for the data generators module."""

from __future__ import annotations

import pytest

from sharingan.data.fields import FieldType, detect_field_type
from sharingan.data.generators import (
    generate_edge_cases,
    generate_invalid_data,
    generate_valid_data,
)


class TestDetectFieldType:
    """Tests for detect_field_type."""

    def test_detect_email_by_type(self) -> None:
        """Should detect email field by type attribute."""
        assert detect_field_type("email") == FieldType.EMAIL

    def test_detect_password_by_type(self) -> None:
        """Should detect password field by type attribute."""
        assert detect_field_type("password") == FieldType.PASSWORD

    def test_detect_confirm_password(self) -> None:
        """Should detect confirm password by label."""
        result = detect_field_type("password", label="Confirm Password")
        assert result == FieldType.CONFIRM_PASSWORD

    def test_detect_confirm_password_by_name(self) -> None:
        """Should detect confirm password by name attribute."""
        result = detect_field_type("password", name="confirmPassword")
        assert result == FieldType.CONFIRM_PASSWORD

    def test_detect_email_by_label(self) -> None:
        """Should detect email by label text."""
        result = detect_field_type("text", label="Email Address")
        assert result == FieldType.EMAIL

    def test_detect_username_by_label(self) -> None:
        """Should detect username by label."""
        result = detect_field_type("text", label="Username")
        assert result == FieldType.USERNAME

    def test_detect_phone_by_type(self) -> None:
        """Should detect phone by type=tel."""
        assert detect_field_type("tel") == FieldType.PHONE

    def test_detect_phone_by_label(self) -> None:
        """Should detect phone by label."""
        assert detect_field_type("text", label="Mobile Number") == FieldType.PHONE

    def test_detect_url(self) -> None:
        """Should detect URL field."""
        assert detect_field_type("url") == FieldType.URL

    def test_detect_number(self) -> None:
        """Should detect number field."""
        assert detect_field_type("number") == FieldType.NUMBER

    def test_detect_date(self) -> None:
        """Should detect date field."""
        assert detect_field_type("date") == FieldType.DATE

    def test_detect_checkbox(self) -> None:
        """Should detect checkbox."""
        assert detect_field_type("checkbox") == FieldType.CHECKBOX

    def test_detect_name_by_label(self) -> None:
        """Should detect name field by label."""
        assert detect_field_type("text", label="First Name") == FieldType.NAME

    def test_default_to_text(self) -> None:
        """Should default to text for unknown fields."""
        assert detect_field_type("text") == FieldType.TEXT


class TestGenerateValidData:
    """Tests for generate_valid_data."""

    def test_email_looks_valid(self) -> None:
        """Generated email should look like a valid email."""
        email = generate_valid_data(FieldType.EMAIL)
        assert "@" in email
        assert "." in email

    def test_password_meets_complexity(self) -> None:
        """Generated password should meet complexity requirements."""
        pwd = generate_valid_data(FieldType.PASSWORD)
        assert len(pwd) >= 8
        assert any(c.isdigit() for c in pwd)
        assert any(c.isupper() for c in pwd)

    def test_phone_is_test_number(self) -> None:
        """Phone should be a reserved test number."""
        phone = generate_valid_data(FieldType.PHONE)
        assert "555" in phone

    def test_url_is_valid(self) -> None:
        """URL should start with https."""
        url = generate_valid_data(FieldType.URL)
        assert url.startswith("https://")

    def test_date_is_iso_format(self) -> None:
        """Date should be in ISO format."""
        date = generate_valid_data(FieldType.DATE)
        parts = date.split("-")
        assert len(parts) == 3


class TestGenerateInvalidData:
    """Tests for generate_invalid_data."""

    def test_email_has_empty_case(self) -> None:
        """Invalid email cases should include empty."""
        cases = generate_invalid_data(FieldType.EMAIL)
        values = [c["value"] for c in cases]
        assert "" in values

    def test_email_has_malformed_cases(self) -> None:
        """Invalid email cases should include malformed emails."""
        cases = generate_invalid_data(FieldType.EMAIL)
        values = [c["value"] for c in cases]
        assert any("notanemail" in v for v in values)

    def test_all_cases_have_expected_error(self) -> None:
        """Every invalid case should specify expected error pattern."""
        for field_type in [FieldType.EMAIL, FieldType.PASSWORD, FieldType.PHONE]:
            cases = generate_invalid_data(field_type)
            for case in cases:
                assert "value" in case
                assert "expected_error_pattern" in case

    def test_password_has_short_case(self) -> None:
        """Password invalid cases should include too-short."""
        cases = generate_invalid_data(FieldType.PASSWORD)
        values = [c["value"] for c in cases]
        assert any(len(v) < 6 for v in values if v)

    def test_confirm_password_has_mismatch(self) -> None:
        """Confirm password should test mismatched values."""
        cases = generate_invalid_data(FieldType.CONFIRM_PASSWORD)
        assert len(cases) > 0


class TestGenerateEdgeCases:
    """Tests for generate_edge_cases."""

    def test_includes_injection_attempts(self) -> None:
        """Edge cases for text should include injection attempts."""
        cases = generate_edge_cases(FieldType.TEXT)
        assert any("'" in c or "<" in c for c in cases)

    def test_email_has_plus_addressing(self) -> None:
        """Email edge cases should include plus-addressing."""
        cases = generate_edge_cases(FieldType.EMAIL)
        assert any("+" in c for c in cases)
