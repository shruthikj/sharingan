"""Generate markdown report from test results."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from sharingan.config import SharinganConfig


def generate_report(results: dict[str, Any], config: SharinganConfig) -> str:
    """Generate a markdown report from test results.

    Args:
        results: Parsed test results dictionary.
        config: Sharingan configuration.

    Returns:
        Rendered markdown report string.
    """
    template_dir = Path(__file__).parent / "templates"
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
    )

    template = env.get_template("report.md.j2")

    # Build template context
    context = _build_context(results, config)
    return template.render(**context)


def _build_context(results: dict[str, Any], config: SharinganConfig) -> dict[str, Any]:
    """Build the template context from results and config."""
    now = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d at %I:%M %p UTC")

    # Categorize tests
    categories: dict[str, dict[str, int]] = {}
    tests = results.get("tests", [])

    for test in tests:
        cat = _categorize_test(test.get("name", ""))
        if cat not in categories:
            categories[cat] = {"total": 0, "passed": 0, "failed": 0, "fixed": 0, "needs_review": 0}
        categories[cat]["total"] += 1
        status = test.get("status", "")
        if status == "passed":
            categories[cat]["passed"] += 1
        elif status == "failed":
            categories[cat]["failed"] += 1
        elif status == "fixed":
            categories[cat]["fixed"] += 1

    # Build summary stats
    total = len(tests)
    passed = sum(1 for t in tests if t.get("status") == "passed")
    failed = sum(1 for t in tests if t.get("status") == "failed")
    fixed = sum(1 for t in tests if t.get("status") == "fixed")
    needs_review = sum(1 for t in tests if t.get("status") == "needs_review")

    # Bugs found
    bugs_found = results.get("bugs_found", [])
    needs_review_list = results.get("needs_review", [])

    return {
        "generated_at": now,
        "base_url": config.base_url,
        "frameworks": ", ".join(config.frameworks) if config.frameworks else "Unknown",
        "routes_found": results.get("routes_found", 0),
        "pages_found": results.get("pages_found", 0),
        "api_endpoints_found": results.get("api_endpoints_found", 0),
        "forms_found": results.get("forms_found", 0),
        "auth_routes": results.get("auth_routes", 0),
        "categories": categories,
        "total": total,
        "passed": passed,
        "failed": failed,
        "fixed": fixed,
        "needs_review": needs_review,
        "bugs_found": bugs_found,
        "needs_review_list": needs_review_list,
        "screenshots_dir": str(config.get_screenshots_path()),
        "duration": results.get("duration", ""),
    }


def _categorize_test(name: str) -> str:
    """Categorize a test by its name."""
    name_lower = name.lower()
    if any(kw in name_lower for kw in ["auth", "login", "signup", "logout"]):
        return "Auth"
    if any(kw in name_lower for kw in ["api_", "endpoint", "health"]):
        return "API"
    if any(kw in name_lower for kw in ["form", "validation", "submission"]):
        return "Forms"
    if any(kw in name_lower for kw in ["a11y", "accessibility"]):
        return "Accessibility"
    if any(kw in name_lower for kw in ["permission", "requires_auth", "guard"]):
        return "Permission"
    return "Navigation"
