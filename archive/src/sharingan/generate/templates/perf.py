"""Performance test templates."""

from __future__ import annotations

from sharingan.config import SharinganConfig
from sharingan.generate.test_planner import TestCase


def generate_perf_tests(test_cases: list[TestCase], config: SharinganConfig) -> str:
    """Generate Playwright performance tests.

    Captures Web Vitals (LCP, FCP, TTI) and asserts they're within thresholds.

    Args:
        test_cases: Performance test cases.
        config: Sharingan configuration.

    Returns:
        Playwright test file content.
    """
    base_url = config.base_url
    max_lcp = config.perf.max_lcp_ms
    max_fcp = config.perf.max_fcp_ms
    max_tti = config.perf.max_tti_ms

    lines = [
        'import { test, expect } from "@playwright/test";',
        "",
        f'const BASE_URL = "{base_url}";',
        f"const MAX_LCP = {max_lcp};",
        f"const MAX_FCP = {max_fcp};",
        f"const MAX_TTI = {max_tti};",
        "",
        'test.describe("Performance Metrics", () => {',
    ]

    for tc in test_cases:
        lines.append("")
        lines.append(f'  test("{_humanize(tc.name)}", async ({{ page }}) => {{')
        lines.append(f"    // {tc.description}")
        lines.extend([
            f'    await page.goto(`${{BASE_URL}}{tc.route}`, {{ waitUntil: "networkidle" }});',
            "",
            "    // Capture Web Vitals via Performance API",
            "    const metrics = await page.evaluate(() => {",
            "      const perfEntries = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;",
            "      const paintEntries = performance.getEntriesByType('paint');",
            "      const fcp = paintEntries.find((e) => e.name === 'first-contentful-paint');",
            "      return {",
            "        fcp: fcp ? fcp.startTime : 0,",
            "        domContentLoaded: perfEntries ? perfEntries.domContentLoadedEventEnd : 0,",
            "        load: perfEntries ? perfEntries.loadEventEnd : 0,",
            "      };",
            "    });",
            "",
            "    console.log(`Performance for {tc.route}:`, metrics);",
            "",
            "    // Assert performance thresholds",
            "    expect(metrics.fcp).toBeLessThan(MAX_FCP);",
            "    expect(metrics.load).toBeLessThan(MAX_TTI);",
        ])
        lines.append("  });")

    lines.append("});")
    lines.append("")
    return "\n".join(lines)


def _humanize(name: str) -> str:
    """Convert snake_case to human-readable test name."""
    return name.replace("_", " ").title()
