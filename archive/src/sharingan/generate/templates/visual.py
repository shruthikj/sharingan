"""Visual regression test templates."""

from __future__ import annotations

from sharingan.config import SharinganConfig
from sharingan.generate.test_planner import TestCase


def generate_visual_tests(test_cases: list[TestCase], config: SharinganConfig) -> str:
    """Generate Playwright visual regression tests using toHaveScreenshot.

    On first run, Playwright captures baseline screenshots. Subsequent runs
    compare against the baselines with configured thresholds.

    Args:
        test_cases: Visual regression test cases.
        config: Sharingan configuration.

    Returns:
        Playwright test file content.
    """
    base_url = config.base_url
    full_page = "true" if config.visual.full_page else "false"
    threshold = config.visual.threshold
    max_diff = config.visual.max_diff_pixels

    lines = [
        'import { test, expect } from "@playwright/test";',
        "",
        f'const BASE_URL = "{base_url}";',
        "",
        "// Visual regression tests — first run captures baselines,",
        "// subsequent runs compare against them.",
        "",
        'test.describe("Visual Regression", () => {',
    ]

    for tc in test_cases:
        lines.append("")
        lines.append(f'  test("{_humanize(tc.name)}", async ({{ page }}) => {{')
        lines.append(f"    // {tc.description}")
        lines.extend([
            f'    await page.goto(`${{BASE_URL}}{tc.route}`);',
            "",
            "    // Wait for page to settle",
            '    await page.waitForLoadState("networkidle", { timeout: 10000 }).catch(() => {});',
            "",
            "    // Mask dynamic content to prevent false positives",
            "    const dynamicSelectors = [",
            '      "[data-testid*=\\"timestamp\\"]",',
            '      "[data-testid*=\\"date\\"]",',
            '      ".timestamp",',
            '      "time",',
            "    ];",
            "",
            f"    await expect(page).toHaveScreenshot(`${{encodeURIComponent('{tc.route}')}}.png`, {{",
            f"      fullPage: {full_page},",
            f"      maxDiffPixels: {max_diff},",
            f"      threshold: {threshold},",
            "      mask: dynamicSelectors.map((sel) => page.locator(sel)),",
            "    });",
        ])
        lines.append("  });")

    lines.append("});")
    lines.append("")
    return "\n".join(lines)


def _humanize(name: str) -> str:
    """Convert snake_case to human-readable test name."""
    return name.replace("_", " ").title()
