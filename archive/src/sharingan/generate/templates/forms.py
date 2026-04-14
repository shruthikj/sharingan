"""Form validation test templates using data generators."""

from __future__ import annotations

from sharingan.config import SharinganConfig
from sharingan.generate.test_planner import TestCase


def generate_form_tests(test_cases: list[TestCase], config: SharinganConfig) -> str:
    """Generate Playwright form tests with valid and invalid data cases.

    Uses detected field types to generate realistic valid data and
    targeted invalid data per field. Tests form validation errors and
    successful submission paths.

    Args:
        test_cases: Form-related test cases.
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
        "// Realistic test data generators",
        "const validData = {",
        '  email: () => `sharingan-test-${Math.floor(Math.random() * 9000 + 1000)}@example.local`,',
        '  password: () => "SharinganT3st!2026",',
        '  name: () => "Alice Smith",',
        '  phone: () => "+15555550100",',
        '  url: () => "https://example.com",',
        '  number: () => "42",',
        '  date: () => "2025-06-15",',
        '  text: () => "Test Value",',
        "};",
        "",
        'test.describe("Form Validation", () => {',
    ]

    for tc in test_cases:
        lines.append("")
        lines.append(f'  test("{_humanize(tc.name)}", async ({{ page }}) => {{')
        lines.append(f"    // {tc.description}")
        lines.append(f'    await page.goto(`${{BASE_URL}}{tc.route}`);')

        if "validation" in tc.name:
            lines.extend([
                "",
                "    // Try submitting empty form to trigger validation",
                '    const submitBtn = page.getByRole("button", { name: /submit|save|send|sign ?up|log ?in|register|create/i });',
                "    await submitBtn.first().click();",
                "",
                "    // Wait for validation errors",
                "    await page.waitForTimeout(500);",
                "",
                "    // Expect validation messages or form to not have submitted",
                "    const errorText = page.getByText(/required|invalid|please|must|error/i);",
                '    const inputsInvalid = await page.locator("input:invalid").count();',
                "    const hasErrors = (await errorText.count()) > 0 || inputsInvalid > 0;",
                "    expect(hasErrors).toBe(true);",
            ])
        elif "invalid_email" in tc.name:
            lines.extend([
                "",
                "    // Fill email with invalid format",
                "    const emailField = page.getByLabel(/email/i);",
                '    if (await emailField.count() > 0) {',
                '      await emailField.first().fill("notanemail");',
                "      const pwd = page.getByLabel(/password/i).first();",
                "      if (await pwd.count() > 0) await pwd.fill(validData.password());",
                "",
                '      await page.getByRole("button", { name: /submit|save|send|sign ?up|log ?in|register/i }).first().click();',
                "      await page.waitForTimeout(500);",
                "",
                "      // Expect to stay on page with error",
                "      const errorVisible = await page.getByText(/invalid|valid email/i).count();",
                '      const stillOnForm = await page.locator("form").count();',
                "      expect(errorVisible > 0 || stillOnForm > 0).toBe(true);",
                "    }",
            ])
        elif "password_mismatch" in tc.name:
            lines.extend([
                "",
                "    // Fill password fields with mismatched values",
                '    const email = page.getByLabel(/email/i).first();',
                '    if (await email.count() > 0) await email.fill(validData.email());',
                "",
                "    const pwd = page.getByLabel(/^password/i).first();",
                "    const confirmPwd = page.getByLabel(/confirm password|repeat password/i).first();",
                "",
                "    if (await confirmPwd.count() > 0) {",
                '      await pwd.fill("SecurePass123!");',
                '      await confirmPwd.fill("DifferentPass456!");',
                '      await page.getByRole("button", { name: /sign ?up|register|submit|create/i }).first().click();',
                "",
                "      await page.waitForTimeout(1000);",
                "",
                "      // Expect mismatch error",
                "      const mismatchError = page.getByText(/match|same|mismatch/i);",
                "      await expect(mismatchError.first()).toBeVisible({ timeout: 3000 });",
                "    } else {",
                "      test.skip();",
                "    }",
            ])
        elif "submission" in tc.name or "happy" in tc.name:
            lines.extend([
                "",
                "    // Fill form with valid data",
                '    const inputs = page.locator("input:visible:not([type=hidden]), textarea:visible, select:visible");',
                "    const count = await inputs.count();",
                "    for (let i = 0; i < count; i++) {",
                "      const input = inputs.nth(i);",
                '      const type = (await input.getAttribute("type")) || "text";',
                '      const name = (await input.getAttribute("name")) || "";',
                '      const id = (await input.getAttribute("id")) || "";',
                "      const context = `${type} ${name} ${id}`.toLowerCase();",
                "",
                '      if (type === "email" || /email/.test(context)) {',
                "        await input.fill(validData.email());",
                '      } else if (type === "password" || /password/.test(context)) {',
                "        await input.fill(validData.password());",
                '      } else if (type === "tel" || /phone/.test(context)) {',
                "        await input.fill(validData.phone());",
                '      } else if (type === "url" || /url|website/.test(context)) {',
                "        await input.fill(validData.url());",
                '      } else if (type === "number" || /age|count/.test(context)) {',
                "        await input.fill(validData.number());",
                '      } else if (type === "date") {',
                "        await input.fill(validData.date());",
                '      } else if (type === "checkbox") {',
                "        await input.check();",
                "      } else {",
                "        await input.fill(validData.name());",
                "      }",
                "    }",
                "",
                "    // Submit the form",
                '    await page.getByRole("button", { name: /submit|save|send|sign ?up|log ?in|register|create/i }).first().click();',
                "",
                "    // Expect some indication of success (URL change or success message)",
                "    await page.waitForTimeout(1500);",
                "    const urlChanged = !page.url().includes(`{tc.route}`);",
                "    const successMsg = await page.getByText(/success|welcome|thank|created|saved/i).count();",
                "    expect(urlChanged || successMsg > 0).toBe(true);",
            ])

        lines.append("  });")

    lines.append("});")
    lines.append("")
    return "\n".join(lines)


def _humanize(name: str) -> str:
    """Convert snake_case to human-readable test name."""
    return name.replace("_", " ").title()
