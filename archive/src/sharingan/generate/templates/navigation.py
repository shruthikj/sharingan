"""Navigation and routing test templates."""

from __future__ import annotations

from sharingan.config import SharinganConfig
from sharingan.generate.test_planner import TestCase


def generate_navigation_tests(test_cases: list[TestCase], config: SharinganConfig) -> str:
    """Generate Playwright navigation test file.

    Args:
        test_cases: Navigation-related test cases.
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
        'test.describe("Navigation & Routing", () => {',
    ]

    for tc in test_cases:
        lines.append("")
        lines.append(f'  test("{_humanize(tc.name)}", async ({{ page }}) => {{')
        lines.append(f"    // {tc.description}")

        # Skip dynamic routes (they need parameter values)
        if ":" in tc.route:
            lines.extend([
                f"    // Dynamic route — skipping in auto-generated test",
                f'    // Route: {tc.route}',
                '    test.skip();',
            ])
        else:
            lines.extend([
                f'    const response = await page.goto(`${{BASE_URL}}{tc.route}`);',
                "    expect(response?.status()).toBeLessThan(400);",
                '    await expect(page).toHaveTitle(/.*/);',
                "",
                "    // Verify no console errors",
                "    const errors: string[] = [];",
                '    page.on("console", (msg) => {',
                '      if (msg.type() === "error") errors.push(msg.text());',
                "    });",
                '    await page.reload();',
                '    expect(errors.length).toBe(0);',
            ])

        lines.append("  });")

    lines.append("});")
    lines.append("")
    return "\n".join(lines)


def generate_permission_tests(test_cases: list[TestCase], config: SharinganConfig) -> str:
    """Generate Playwright permission/auth-guard test file.

    Args:
        test_cases: Permission-related test cases.
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
        'test.describe("Permission & Auth Guards", () => {',
    ]

    for tc in test_cases:
        lines.append("")
        lines.append(f'  test("{_humanize(tc.name)}", async ({{ page }}) => {{')
        lines.append(f"    // {tc.description}")
        lines.extend([
            f"    // Access protected route without authentication",
            f'    await page.goto(`${{BASE_URL}}{tc.route}`);',
            "",
            "    // Should redirect to login or show unauthorized",
            '    await expect(page).toHaveURL(/login|signin|unauthorized|403/);',
        ])
        lines.append("  });")

    lines.append("});")
    lines.append("")
    return "\n".join(lines)


def _humanize(name: str) -> str:
    """Convert snake_case to human-readable test name."""
    return name.replace("_", " ").title()
