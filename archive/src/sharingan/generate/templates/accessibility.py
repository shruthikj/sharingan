"""Basic accessibility check test templates."""

from __future__ import annotations

from sharingan.config import SharinganConfig
from sharingan.generate.test_planner import TestCase


def generate_accessibility_tests(test_cases: list[TestCase], config: SharinganConfig) -> str:
    """Generate Playwright accessibility test file.

    Args:
        test_cases: Accessibility-related test cases.
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
        'test.describe("Accessibility Basics", () => {',
    ]

    for tc in test_cases:
        lines.append("")
        lines.append(f'  test("{_humanize(tc.name)}", async ({{ page }}) => {{')
        lines.append(f"    // {tc.description}")
        lines.extend([
            f'    await page.goto(`${{BASE_URL}}{tc.route}`);',
            "",
            "    // Check for at least one heading",
            '    const headings = page.locator("h1, h2, h3, h4, h5, h6");',
            "    await expect(headings.first()).toBeVisible();",
            "",
            "    // Check all images have alt text",
            '    const images = page.locator("img");',
            "    const imgCount = await images.count();",
            "    for (let i = 0; i < imgCount; i++) {",
            '      const alt = await images.nth(i).getAttribute("alt");',
            "      expect(alt).toBeTruthy();",
            "    }",
            "",
            "    // Check page has a lang attribute",
            '    const lang = await page.locator("html").getAttribute("lang");',
            "    expect(lang).toBeTruthy();",
            "",
            "    // Check for skip navigation or main landmark",
            '    const main = page.locator("main, [role=\\"main\\"]");',
            "    await expect(main).toBeVisible();",
        ])
        lines.append("  });")

    lines.append("});")
    lines.append("")
    return "\n".join(lines)


def _humanize(name: str) -> str:
    """Convert snake_case to human-readable test name."""
    return name.replace("_", " ").title()
