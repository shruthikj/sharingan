"""Authenticated flow test templates."""

from __future__ import annotations

from sharingan.config import SharinganConfig
from sharingan.generate.test_planner import TestCase


def generate_authenticated_tests(test_cases: list[TestCase], config: SharinganConfig) -> str:
    """Generate Playwright authenticated flow tests.

    These tests assume the user is already logged in (via storage state)
    and test the authenticated portions of the application.

    Args:
        test_cases: Authenticated flow test cases.
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
        "// These tests run with storageState from auth.setup.ts",
        "// They assume the test user is already logged in.",
        "",
        'test.describe("Authenticated Flows", () => {',
    ]

    for tc in test_cases:
        lines.append("")
        lines.append(f'  test("{_humanize(tc.name)}", async ({{ page }}) => {{')
        lines.append(f"    // {tc.description}")

        if "logout" in tc.name.lower():
            lines.extend([
                f'    await page.goto(`${{BASE_URL}}/`);',
                "",
                "    // Find and click the logout button",
                '    const logoutBtn = page.getByRole("button", { name: /log ?out|sign ?out/i })',
                '      .or(page.getByRole("link", { name: /log ?out|sign ?out/i }));',
                "    await logoutBtn.first().click();",
                "",
                "    // After logout, protected routes should redirect",
                '    await page.goto(`${BASE_URL}/dashboard`);',
                '    await expect(page).toHaveURL(/login|signin|\\/$/);',
            ])
        elif "access_dashboard" in tc.name or "visit_dashboard" in tc.name:
            lines.extend([
                f'    await page.goto(`${{BASE_URL}}{tc.route}`);',
                "    // Should NOT redirect to login since we are authenticated",
                '    await expect(page).not.toHaveURL(/login|signin/);',
                '    await expect(page.locator("body")).toBeVisible();',
            ])
        elif "session_persists" in tc.name:
            lines.extend([
                f'    await page.goto(`${{BASE_URL}}{tc.route}`);',
                '    await expect(page).not.toHaveURL(/login|signin/);',
                "    // Reload the page to verify session persists",
                "    await page.reload();",
                '    await expect(page).not.toHaveURL(/login|signin/);',
            ])
        else:
            lines.extend([
                f'    await page.goto(`${{BASE_URL}}{tc.route}`);',
                "    // Authenticated test — should reach the target page",
                '    await expect(page).not.toHaveURL(/login|signin/);',
                '    await expect(page.locator("body")).toBeVisible();',
            ])

        lines.append("  });")

    lines.append("});")
    lines.append("")
    return "\n".join(lines)


def _humanize(name: str) -> str:
    """Convert snake_case to human-readable test name."""
    return name.replace("_", " ").title()
