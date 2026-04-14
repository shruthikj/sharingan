"""API endpoint test templates."""

from __future__ import annotations

from sharingan.config import SharinganConfig
from sharingan.generate.test_planner import TestCase


def generate_api_tests(test_cases: list[TestCase], config: SharinganConfig) -> str:
    """Generate Playwright API test file.

    Args:
        test_cases: API-related test cases.
        config: Sharingan configuration.

    Returns:
        Playwright test file content.
    """
    api_url = config.api_base_url
    lines = [
        'import { test, expect } from "@playwright/test";',
        "",
        f'const API_URL = "{api_url}";',
        "",
        'test.describe("API Endpoints", () => {',
    ]

    for tc in test_cases:
        lines.append("")
        lines.append(f'  test("{_humanize(tc.name)}", async ({{ request }}) => {{')
        lines.append(f"    // {tc.description}")

        route = tc.route
        method = tc.method.lower()

        if "invalid_body" in tc.name:
            lines.extend([
                f'    const response = await request.{method}(`${{API_URL}}{route}`, {{',
                "      data: {},",
                "    });",
                "    expect([400, 422]).toContain(response.status());",
            ])
        elif method in ("post", "put", "patch"):
            lines.extend([
                f'    const response = await request.{method}(`${{API_URL}}{route}`, {{',
                "      data: {",
                '        // TODO: Fill with valid request body',
                "      },",
                "    });",
                "    expect(response.status()).toBeLessThan(400);",
                "    const body = await response.json();",
                "    expect(body).toBeTruthy();",
            ])
        else:
            lines.extend([
                f'    const response = await request.{method}(`${{API_URL}}{route}`);',
                "    expect(response.status()).toBeLessThan(400);",
                "    const body = await response.json();",
                "    expect(body).toBeTruthy();",
            ])

        lines.append("  });")

    lines.append("});")
    lines.append("")
    return "\n".join(lines)


def _humanize(name: str) -> str:
    """Convert snake_case to human-readable test name."""
    return name.replace("_", " ").title()
