"""Detect and parse OpenAPI specifications."""

from __future__ import annotations

import json
from typing import Any
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from pydantic import BaseModel, Field


class OpenAPIEndpoint(BaseModel):
    """A single endpoint from an OpenAPI spec."""

    path: str = Field(description="Path template (e.g., /users/{id})")
    method: str = Field(description="HTTP method")
    response_schemas: dict[str, Any] = Field(
        default_factory=dict,
        description="Response schemas by status code",
    )


class OpenAPISpec(BaseModel):
    """A parsed OpenAPI specification."""

    version: str = Field(description="OpenAPI version")
    title: str = Field(default="", description="API title")
    endpoints: list[OpenAPIEndpoint] = Field(default_factory=list, description="All endpoints")

    def find_endpoint(self, path: str, method: str) -> OpenAPIEndpoint | None:
        """Find an endpoint by path and method."""
        method_upper = method.upper()
        for ep in self.endpoints:
            if ep.method.upper() == method_upper and _path_matches(ep.path, path):
                return ep
        return None


def find_openapi_spec(base_url: str, candidate_paths: list[str], timeout: int = 5) -> dict[str, Any] | None:
    """Search for an OpenAPI spec at common paths.

    Args:
        base_url: Base URL of the API server.
        candidate_paths: List of paths to try (e.g., ["/openapi.json"]).
        timeout: Request timeout in seconds.

    Returns:
        Parsed JSON dict if found, None otherwise.
    """
    for path in candidate_paths:
        url = urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))
        try:
            req = Request(url, headers={"Accept": "application/json"})
            with urlopen(req, timeout=timeout) as response:
                if response.status == 200:
                    return json.loads(response.read())
        except Exception:
            continue
    return None


def parse_openapi_spec(spec_data: dict[str, Any]) -> OpenAPISpec:
    """Parse an OpenAPI spec dict into a structured object.

    Args:
        spec_data: The raw OpenAPI JSON as a dict.

    Returns:
        Parsed OpenAPISpec.
    """
    version = spec_data.get("openapi") or spec_data.get("swagger") or "unknown"
    info = spec_data.get("info", {})
    title = info.get("title", "")

    endpoints: list[OpenAPIEndpoint] = []
    paths = spec_data.get("paths", {})

    for path, path_obj in paths.items():
        for method in ["get", "post", "put", "patch", "delete", "head", "options"]:
            if method in path_obj:
                operation = path_obj[method]
                response_schemas = _extract_response_schemas(operation)
                endpoints.append(OpenAPIEndpoint(
                    path=path,
                    method=method.upper(),
                    response_schemas=response_schemas,
                ))

    return OpenAPISpec(version=version, title=title, endpoints=endpoints)


def _extract_response_schemas(operation: dict[str, Any]) -> dict[str, Any]:
    """Extract response schemas keyed by status code."""
    schemas: dict[str, Any] = {}
    responses = operation.get("responses", {})

    for status_code, response_obj in responses.items():
        # OpenAPI 3.x: responses.{code}.content.{type}.schema
        content = response_obj.get("content", {})
        for content_type, content_obj in content.items():
            if "json" in content_type:
                schema = content_obj.get("schema")
                if schema:
                    schemas[str(status_code)] = schema
                    break

        # OpenAPI 2.x fallback: responses.{code}.schema
        if str(status_code) not in schemas and "schema" in response_obj:
            schemas[str(status_code)] = response_obj["schema"]

    return schemas


def _path_matches(template: str, actual: str) -> bool:
    """Check if an actual path matches a template with path params.

    E.g., template "/users/{id}" matches actual "/users/123".
    """
    template_parts = template.strip("/").split("/")
    actual_parts = actual.strip("/").split("/")

    if len(template_parts) != len(actual_parts):
        return False

    for t, a in zip(template_parts, actual_parts):
        if t.startswith("{") and t.endswith("}"):
            continue
        if t != a:
            return False

    return True
