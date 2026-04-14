"""Tests for report generation."""

from __future__ import annotations

from pathlib import Path

import pytest

from sharingan.config import SharinganConfig
from sharingan.report.generator import generate_report


@pytest.fixture
def config(tmp_path: Path) -> SharinganConfig:
    """Create a test configuration."""
    return SharinganConfig(
        project_dir=tmp_path,
        frameworks=["nextjs", "fastapi"],
    )


@pytest.fixture
def sample_results() -> dict:
    """Create sample test results for report generation."""
    return {
        "routes_found": 12,
        "pages_found": 8,
        "api_endpoints_found": 4,
        "forms_found": 3,
        "auth_routes": 5,
        "tests": [
            {"name": "home_page_loads", "status": "passed"},
            {"name": "login_page_loads", "status": "passed"},
            {"name": "login_valid_credentials", "status": "passed"},
            {"name": "signup_happy_path", "status": "fixed"},
            {"name": "dashboard_requires_auth", "status": "fixed"},
            {"name": "api_health_get_success", "status": "passed"},
            {"name": "api_items_post_invalid_body", "status": "fixed"},
            {"name": "settings_timezone", "status": "needs_review"},
        ],
        "bugs_found": [
            {
                "title": "Signup form missing password confirmation",
                "file": "src/app/signup/page.tsx",
                "issue": "Form submits without confirming password match",
                "fix": "Added password confirmation check",
                "status": "Fixed and verified",
            },
            {
                "title": "Dashboard accessible without auth",
                "file": "src/middleware.ts",
                "issue": "No auth check on /dashboard",
                "fix": "Added auth guard",
                "status": "Fixed and verified",
            },
        ],
        "needs_review": [
            {
                "title": "Settings timezone selector",
                "file": "src/app/settings/page.tsx",
                "issue": "Timezone doesn't update after save",
                "attempts": 3,
            },
        ],
        "duration": "45s",
    }


class TestGenerateReport:
    """Tests for generate_report."""

    def test_generates_markdown(self, sample_results: dict, config: SharinganConfig) -> None:
        """Should generate a valid markdown report."""
        report = generate_report(sample_results, config)
        assert isinstance(report, str)
        assert len(report) > 0
        assert "# Sharingan Report" in report

    def test_includes_framework_info(self, sample_results: dict, config: SharinganConfig) -> None:
        """Should include detected frameworks."""
        report = generate_report(sample_results, config)
        assert "nextjs" in report
        assert "fastapi" in report

    def test_includes_discovery_stats(self, sample_results: dict, config: SharinganConfig) -> None:
        """Should include route discovery statistics."""
        report = generate_report(sample_results, config)
        assert "12" in report  # routes_found
        assert "8" in report   # pages
        assert "4" in report   # api endpoints

    def test_includes_test_results_table(self, sample_results: dict, config: SharinganConfig) -> None:
        """Should include a test results table."""
        report = generate_report(sample_results, config)
        assert "| Category" in report
        assert "Passed" in report
        assert "Failed" in report

    def test_includes_bugs_found(self, sample_results: dict, config: SharinganConfig) -> None:
        """Should list bugs found and fixed."""
        report = generate_report(sample_results, config)
        assert "Bugs Found" in report
        assert "password confirmation" in report.lower() or "Signup" in report

    def test_includes_needs_review(self, sample_results: dict, config: SharinganConfig) -> None:
        """Should list items needing human review."""
        report = generate_report(sample_results, config)
        assert "Human Review" in report
        assert "timezone" in report.lower() or "Settings" in report

    def test_empty_results(self, config: SharinganConfig) -> None:
        """Should handle empty results gracefully."""
        report = generate_report({"tests": []}, config)
        assert "# Sharingan Report" in report
        assert "**0**" in report

    def test_includes_screenshots_reference(self, sample_results: dict, config: SharinganConfig) -> None:
        """Should reference the screenshots directory."""
        report = generate_report(sample_results, config)
        assert "screenshots" in report.lower()
