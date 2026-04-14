"""Parse Playwright JSON test results."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class TestResult(BaseModel):
    """Result of a single test case."""

    name: str = Field(description="Test name")
    status: str = Field(description="Test status: passed, failed, skipped, timedOut")
    duration_ms: int = Field(default=0, description="Duration in milliseconds")
    error_message: str = Field(default="", description="Error message if failed")
    error_snippet: str = Field(default="", description="Code snippet at failure point")
    file_path: str = Field(default="", description="Test file path")
    screenshot_path: str = Field(default="", description="Screenshot path if captured")
    retry_count: int = Field(default=0, description="Number of retries attempted")


class TestSuiteResults(BaseModel):
    """Aggregated results of a test suite run."""

    total: int = Field(default=0)
    passed: int = Field(default=0)
    failed: int = Field(default=0)
    skipped: int = Field(default=0)
    timed_out: int = Field(default=0)
    duration_ms: int = Field(default=0)
    tests: list[TestResult] = Field(default_factory=list)

    @property
    def pass_rate(self) -> float:
        """Calculate the pass rate as a percentage."""
        if self.total == 0:
            return 0.0
        return (self.passed / self.total) * 100

    @property
    def failing_tests(self) -> list[TestResult]:
        """Get all failing tests."""
        return [t for t in self.tests if t.status == "failed"]


def parse_playwright_results(results_path: Path) -> TestSuiteResults:
    """Parse Playwright JSON reporter output into structured results.

    Args:
        results_path: Path to the JSON results file.

    Returns:
        Parsed test suite results.
    """
    if not results_path.exists():
        return TestSuiteResults()

    try:
        data = json.loads(results_path.read_text())
    except (json.JSONDecodeError, OSError):
        return TestSuiteResults()

    return _parse_json_report(data)


def _parse_json_report(data: dict[str, Any]) -> TestSuiteResults:
    """Parse the Playwright JSON report structure."""
    results = TestSuiteResults()

    suites = data.get("suites", [])
    for suite in suites:
        _parse_suite(suite, results)

    results.total = len(results.tests)
    results.passed = sum(1 for t in results.tests if t.status == "passed")
    results.failed = sum(1 for t in results.tests if t.status == "failed")
    results.skipped = sum(1 for t in results.tests if t.status == "skipped")
    results.timed_out = sum(1 for t in results.tests if t.status == "timedOut")

    stats = data.get("stats", {})
    results.duration_ms = stats.get("duration", 0)

    return results


def _parse_suite(suite: dict[str, Any], results: TestSuiteResults) -> None:
    """Recursively parse a test suite and its specs."""
    file_path = suite.get("file", "")

    for spec in suite.get("specs", []):
        test_result = _parse_spec(spec, file_path)
        results.tests.append(test_result)

    for child_suite in suite.get("suites", []):
        _parse_suite(child_suite, results)


def _parse_spec(spec: dict[str, Any], file_path: str) -> TestResult:
    """Parse a single test spec."""
    title = spec.get("title", "unknown")

    # Get the last test result (after retries)
    tests = spec.get("tests", [{}])
    last_test = tests[-1] if tests else {}

    results = last_test.get("results", [{}])
    last_result = results[-1] if results else {}

    status = last_result.get("status", "unknown")
    duration = last_result.get("duration", 0)

    error_message = ""
    error_snippet = ""
    if status == "failed":
        error = last_result.get("error", {})
        error_message = error.get("message", "")
        error_snippet = error.get("snippet", "")

    screenshot_path = ""
    for attachment in last_result.get("attachments", []):
        if attachment.get("name") == "screenshot":
            screenshot_path = attachment.get("path", "")
            break

    return TestResult(
        name=title,
        status=status,
        duration_ms=duration,
        error_message=error_message,
        error_snippet=error_snippet,
        file_path=file_path,
        screenshot_path=screenshot_path,
        retry_count=len(results) - 1,
    )
