"""Auth flow test templates (signup, login, logout, forgot password)."""

from __future__ import annotations

from sharingan.config import SharinganConfig
from sharingan.generate.test_planner import TestCase


def generate_auth_tests(test_cases: list[TestCase], config: SharinganConfig) -> str:
    """Generate Playwright auth test file.

    Args:
        test_cases: Auth-related test cases.
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
        'test.describe("Authentication Flows", () => {',
    ]

    for tc in test_cases:
        lines.append("")
        lines.append(f'  test("{_humanize(tc.name)}", async ({{ page }}) => {{')
        lines.append(f"    // {tc.description}")

        if "signup_happy_path" in tc.name:
            lines.extend([
                f'    await page.goto(`${{BASE_URL}}{tc.route}`);',
                '    await page.getByLabel("Email").fill("testuser@example.com");',
                '    await page.getByLabel("Password", { exact: true }).fill("SecurePass123!");',
                '    await page.getByLabel("Confirm Password").fill("SecurePass123!");',
                '    await page.getByRole("button", { name: /sign up|register/i }).click();',
                '    await expect(page).toHaveURL(/dashboard|home|\\//);',
            ])
        elif "signup_existing" in tc.name:
            lines.extend([
                f'    await page.goto(`${{BASE_URL}}{tc.route}`);',
                '    await page.getByLabel("Email").fill("existing@example.com");',
                '    await page.getByLabel("Password", { exact: true }).fill("SecurePass123!");',
                '    await page.getByRole("button", { name: /sign up|register/i }).click();',
                '    await expect(page.getByText(/already exists|already registered/i)).toBeVisible();',
            ])
        elif "login_valid" in tc.name:
            lines.extend([
                f'    await page.goto(`${{BASE_URL}}{tc.route}`);',
                '    await page.getByLabel("Email").fill("testuser@example.com");',
                '    await page.getByLabel("Password").fill("SecurePass123!");',
                '    await page.getByRole("button", { name: /log in|sign in/i }).click();',
                '    await expect(page).toHaveURL(/dashboard|home/);',
            ])
        elif "login_invalid" in tc.name:
            lines.extend([
                f'    await page.goto(`${{BASE_URL}}{tc.route}`);',
                '    await page.getByLabel("Email").fill("testuser@example.com");',
                '    await page.getByLabel("Password").fill("wrongpassword");',
                '    await page.getByRole("button", { name: /log in|sign in/i }).click();',
                '    await expect(page.getByText(/invalid|incorrect|wrong/i)).toBeVisible();',
            ])
        elif "logout" in tc.name:
            lines.extend([
                f"    await page.goto(`${{BASE_URL}}/login`);",
                '    await page.getByLabel("Email").fill("testuser@example.com");',
                '    await page.getByLabel("Password").fill("SecurePass123!");',
                '    await page.getByRole("button", { name: /log in|sign in/i }).click();',
                '    await expect(page).toHaveURL(/dashboard|home/);',
                '    await page.getByRole("button", { name: /log out|sign out/i }).click();',
                '    await expect(page).toHaveURL(/login|\\/$/);\n',
            ])
        else:
            lines.extend([
                f'    await page.goto(`${{BASE_URL}}{tc.route}`);',
                "    // TODO: Implement test logic",
                '    await expect(page).toHaveTitle(/.+/);',
            ])

        lines.append("  });")

    lines.append("});")
    lines.append("")
    return "\n".join(lines)


def _humanize(name: str) -> str:
    """Convert snake_case to human-readable test name."""
    return name.replace("_", " ").title()
