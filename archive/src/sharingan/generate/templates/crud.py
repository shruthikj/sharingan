"""CRUD operation test templates."""

from __future__ import annotations

from sharingan.config import SharinganConfig
from sharingan.generate.test_planner import TestCase


def generate_crud_tests(test_cases: list[TestCase], config: SharinganConfig) -> str:
    """Generate Playwright CRUD test file.

    Args:
        test_cases: CRUD-related test cases.
        config: Sharingan configuration.

    Returns:
        Playwright test file content.
    """
    base_url = config.base_url
    lines = [
        'import { test, expect } from "@playwright/test";',
        "",
        f'const BASE_URL = "{base_url}";',
        "",
        'test.describe("CRUD Operations", () => {',
    ]

    for tc in test_cases:
        lines.append("")
        lines.append(f'  test("{_humanize(tc.name)}", async ({{ page }}) => {{')
        lines.append(f"    // {tc.description}")
        lines.extend([
            f'    await page.goto(`${{BASE_URL}}{tc.route}`);',
            "    // TODO: Implement CRUD test logic based on discovered models",
            '    await expect(page).toHaveTitle(/.+/);',
        ])
        lines.append("  });")

    lines.append("});")
    lines.append("")
    return "\n".join(lines)


def _humanize(name: str) -> str:
    """Convert snake_case to human-readable test name."""
    return name.replace("_", " ").title()
