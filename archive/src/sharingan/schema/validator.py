"""Validate API responses against JSON schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ValidationResult(BaseModel):
    """Result of validating a response against a schema."""

    valid: bool = Field(description="Whether validation passed")
    errors: list[str] = Field(default_factory=list, description="Validation errors")


def validate_response(response_body: Any, schema: dict[str, Any]) -> ValidationResult:
    """Validate a response body against a JSON schema.

    Performs a lightweight validation without requiring jsonschema library.
    Checks type, required fields, and recursive structure for objects/arrays.

    Args:
        response_body: The actual response body.
        schema: The JSON schema to validate against.

    Returns:
        ValidationResult with validity and any errors.
    """
    errors: list[str] = []
    _validate(response_body, schema, "$", errors)
    return ValidationResult(valid=not errors, errors=errors)


def _validate(value: Any, schema: dict[str, Any], path: str, errors: list[str]) -> None:
    """Recursively validate a value against a schema."""
    if not schema:
        return

    expected_type = schema.get("type")

    if expected_type:
        if not _check_type(value, expected_type):
            errors.append(f"{path}: expected {expected_type}, got {type(value).__name__}")
            return

    if expected_type == "object" and isinstance(value, dict):
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        for req_key in required:
            if req_key not in value:
                errors.append(f"{path}.{req_key}: required property missing")

        for key, prop_schema in properties.items():
            if key in value:
                _validate(value[key], prop_schema, f"{path}.{key}", errors)

    elif expected_type == "array" and isinstance(value, list):
        items_schema = schema.get("items", {})
        if items_schema:
            for i, item in enumerate(value):
                _validate(item, items_schema, f"{path}[{i}]", errors)


def _check_type(value: Any, expected: str) -> bool:
    """Check if a value matches a JSON schema type."""
    type_map = {
        "null": lambda v: v is None,
        "boolean": lambda v: isinstance(v, bool),
        "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
        "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
        "string": lambda v: isinstance(v, str),
        "array": lambda v: isinstance(v, list),
        "object": lambda v: isinstance(v, dict),
    }
    check = type_map.get(expected)
    return bool(check(value)) if check else True
