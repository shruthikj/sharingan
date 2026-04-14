"""Infer JSON schemas from sample API responses."""

from __future__ import annotations

from typing import Any


def infer_schema_from_response(response_body: Any) -> dict[str, Any]:
    """Infer a simple JSON schema from a sample response.

    Produces a lightweight schema that captures the type and shape of
    the response, suitable for validating that subsequent responses have
    the same structure.

    Args:
        response_body: Parsed response body (dict, list, or primitive).

    Returns:
        A JSON Schema dict describing the response structure.
    """
    return _infer_type(response_body)


def _infer_type(value: Any) -> dict[str, Any]:
    """Recursively infer the JSON schema type of a value."""
    if value is None:
        return {"type": "null"}

    if isinstance(value, bool):
        return {"type": "boolean"}

    if isinstance(value, int):
        return {"type": "integer"}

    if isinstance(value, float):
        return {"type": "number"}

    if isinstance(value, str):
        return {"type": "string"}

    if isinstance(value, list):
        if not value:
            return {"type": "array", "items": {}}
        # Infer item type from the first element
        return {"type": "array", "items": _infer_type(value[0])}

    if isinstance(value, dict):
        properties: dict[str, Any] = {}
        required: list[str] = []
        for key, val in value.items():
            properties[key] = _infer_type(val)
            if val is not None:
                required.append(key)
        return {
            "type": "object",
            "properties": properties,
            "required": required,
        }

    return {}
