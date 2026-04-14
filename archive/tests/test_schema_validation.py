"""Tests for the schema validation module."""

from __future__ import annotations

from sharingan.schema.inferrer import infer_schema_from_response
from sharingan.schema.openapi import parse_openapi_spec
from sharingan.schema.validator import validate_response


class TestInferSchema:
    """Tests for infer_schema_from_response."""

    def test_infer_object_schema(self) -> None:
        """Should infer schema for a simple object."""
        response = {"id": 1, "name": "Alice", "active": True}
        schema = infer_schema_from_response(response)
        assert schema["type"] == "object"
        assert schema["properties"]["id"]["type"] == "integer"
        assert schema["properties"]["name"]["type"] == "string"
        assert schema["properties"]["active"]["type"] == "boolean"

    def test_infer_array_schema(self) -> None:
        """Should infer schema for an array."""
        response = [{"id": 1}, {"id": 2}]
        schema = infer_schema_from_response(response)
        assert schema["type"] == "array"
        assert schema["items"]["type"] == "object"

    def test_infer_nested_schema(self) -> None:
        """Should infer nested object schemas."""
        response = {"user": {"id": 1, "email": "a@b.com"}}
        schema = infer_schema_from_response(response)
        assert schema["type"] == "object"
        assert schema["properties"]["user"]["type"] == "object"
        assert "email" in schema["properties"]["user"]["properties"]

    def test_infer_null_type(self) -> None:
        """Should handle null values."""
        schema = infer_schema_from_response(None)
        assert schema["type"] == "null"

    def test_infer_primitives(self) -> None:
        """Should handle primitive types."""
        assert infer_schema_from_response(42)["type"] == "integer"
        assert infer_schema_from_response(3.14)["type"] == "number"
        assert infer_schema_from_response("hello")["type"] == "string"
        assert infer_schema_from_response(True)["type"] == "boolean"


class TestValidateResponse:
    """Tests for validate_response."""

    def test_valid_response(self) -> None:
        """Valid response should pass validation."""
        schema = {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "name": {"type": "string"},
            },
            "required": ["id", "name"],
        }
        response = {"id": 1, "name": "Alice"}
        result = validate_response(response, schema)
        assert result.valid is True
        assert len(result.errors) == 0

    def test_missing_required_field(self) -> None:
        """Missing required field should fail."""
        schema = {
            "type": "object",
            "properties": {"id": {"type": "integer"}},
            "required": ["id"],
        }
        response = {}
        result = validate_response(response, schema)
        assert result.valid is False
        assert any("required" in err for err in result.errors)

    def test_wrong_type(self) -> None:
        """Wrong type should fail validation."""
        schema = {
            "type": "object",
            "properties": {"id": {"type": "integer"}},
        }
        response = {"id": "not an integer"}
        result = validate_response(response, schema)
        assert result.valid is False

    def test_nested_validation(self) -> None:
        """Should validate nested objects."""
        schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "email": {"type": "string"},
                    },
                    "required": ["email"],
                }
            },
        }
        response = {"user": {"email": "test@example.com"}}
        result = validate_response(response, schema)
        assert result.valid is True

    def test_array_validation(self) -> None:
        """Should validate arrays."""
        schema = {
            "type": "array",
            "items": {"type": "integer"},
        }
        result = validate_response([1, 2, 3], schema)
        assert result.valid is True

        result = validate_response([1, "two", 3], schema)
        assert result.valid is False


class TestParseOpenAPISpec:
    """Tests for parse_openapi_spec."""

    def test_parses_basic_spec(self) -> None:
        """Should parse a minimal OpenAPI spec."""
        spec_data = {
            "openapi": "3.0.0",
            "info": {"title": "Test API"},
            "paths": {
                "/users": {
                    "get": {
                        "responses": {
                            "200": {
                                "content": {
                                    "application/json": {
                                        "schema": {"type": "array"}
                                    }
                                }
                            }
                        }
                    }
                }
            },
        }
        spec = parse_openapi_spec(spec_data)
        assert spec.title == "Test API"
        assert len(spec.endpoints) == 1
        assert spec.endpoints[0].path == "/users"
        assert spec.endpoints[0].method == "GET"

    def test_find_endpoint(self) -> None:
        """Should find an endpoint by path and method."""
        spec_data = {
            "openapi": "3.0.0",
            "info": {"title": "Test"},
            "paths": {
                "/users/{id}": {
                    "get": {"responses": {"200": {}}},
                }
            },
        }
        spec = parse_openapi_spec(spec_data)
        assert spec.find_endpoint("/users/123", "GET") is not None
        assert spec.find_endpoint("/users/123", "POST") is None

    def test_handles_multiple_methods(self) -> None:
        """Should extract multiple methods per path."""
        spec_data = {
            "openapi": "3.0.0",
            "info": {},
            "paths": {
                "/items": {
                    "get": {"responses": {}},
                    "post": {"responses": {}},
                    "delete": {"responses": {}},
                }
            },
        }
        spec = parse_openapi_spec(spec_data)
        methods = {ep.method for ep in spec.endpoints}
        assert methods == {"GET", "POST", "DELETE"}
