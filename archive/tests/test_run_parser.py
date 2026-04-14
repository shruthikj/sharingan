"""Tests for Playwright result parser."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sharingan.run.parser import TestSuiteResults, parse_playwright_results


@pytest.fixture
def sample_results_json(tmp_path: Path) -> Path:
    """Create a sample Playwright JSON results file."""
    data = {
        "stats": {
            "startTime": "2026-04-12T22:00:00.000Z",
            "duration": 12500,
        },
        "suites": [
            {
                "title": "Navigation & Routing",
                "file": "tests/sharingan/navigation.spec.ts",
                "specs": [
                    {
                        "title": "Home Page Loads",
                        "tests": [
                            {
                                "results": [
                                    {"status": "passed", "duration": 1200}
                                ]
                            }
                        ],
                    },
                    {
                        "title": "Login Page Loads",
                        "tests": [
                            {
                                "results": [
                                    {"status": "passed", "duration": 800}
                                ]
                            }
                        ],
                    },
                ],
                "suites": [
                    {
                        "title": "Auth Tests",
                        "file": "tests/sharingan/auth.spec.ts",
                        "specs": [
                            {
                                "title": "Login Valid Credentials",
                                "tests": [
                                    {
                                        "results": [
                                            {"status": "passed", "duration": 2500}
                                        ]
                                    }
                                ],
                            },
                            {
                                "title": "Signup Happy Path",
                                "tests": [
                                    {
                                        "results": [
                                            {
                                                "status": "failed",
                                                "duration": 3000,
                                                "error": {
                                                    "message": "Expected element to be visible",
                                                    "snippet": "  await expect(page.getByText('error')).toBeVisible();"
                                                },
                                            }
                                        ]
                                    }
                                ],
                            },
                        ],
                    }
                ],
            },
            {
                "title": "API Endpoints",
                "file": "tests/sharingan/api.spec.ts",
                "specs": [
                    {
                        "title": "Health Endpoint",
                        "tests": [
                            {
                                "results": [
                                    {"status": "passed", "duration": 200}
                                ]
                            }
                        ],
                    },
                    {
                        "title": "Create Item Invalid Body",
                        "tests": [
                            {
                                "results": [
                                    {
                                        "status": "failed",
                                        "duration": 500,
                                        "error": {
                                            "message": "expect(received).toContain(expected)\nExpected: 400 or 422\nReceived: 500",
                                            "snippet": "  expect([400, 422]).toContain(response.status());"
                                        },
                                    }
                                ]
                            }
                        ],
                    },
                ],
            },
        ],
    }

    results_path = tmp_path / "results.json"
    results_path.write_text(json.dumps(data))
    return results_path


class TestParsePlaywrightResults:
    """Tests for parse_playwright_results."""

    def test_parse_valid_results(self, sample_results_json: Path) -> None:
        """Should parse a valid JSON results file."""
        results = parse_playwright_results(sample_results_json)
        assert isinstance(results, TestSuiteResults)
        assert results.total == 6

    def test_count_passed(self, sample_results_json: Path) -> None:
        """Should correctly count passed tests."""
        results = parse_playwright_results(sample_results_json)
        assert results.passed == 4

    def test_count_failed(self, sample_results_json: Path) -> None:
        """Should correctly count failed tests."""
        results = parse_playwright_results(sample_results_json)
        assert results.failed == 2

    def test_failing_tests_list(self, sample_results_json: Path) -> None:
        """Should return list of failing tests."""
        results = parse_playwright_results(sample_results_json)
        failing = results.failing_tests
        assert len(failing) == 2
        names = {t.name for t in failing}
        assert "Signup Happy Path" in names
        assert "Create Item Invalid Body" in names

    def test_error_messages_captured(self, sample_results_json: Path) -> None:
        """Should capture error messages for failing tests."""
        results = parse_playwright_results(sample_results_json)
        for test in results.failing_tests:
            assert test.error_message != ""

    def test_pass_rate(self, sample_results_json: Path) -> None:
        """Should calculate pass rate correctly."""
        results = parse_playwright_results(sample_results_json)
        assert abs(results.pass_rate - 66.67) < 0.1

    def test_duration(self, sample_results_json: Path) -> None:
        """Should capture total duration."""
        results = parse_playwright_results(sample_results_json)
        assert results.duration_ms == 12500

    def test_nonexistent_file(self, tmp_path: Path) -> None:
        """Should return empty results for nonexistent file."""
        results = parse_playwright_results(tmp_path / "nonexistent.json")
        assert results.total == 0

    def test_invalid_json(self, tmp_path: Path) -> None:
        """Should return empty results for invalid JSON."""
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("not valid json {{{")
        results = parse_playwright_results(bad_file)
        assert results.total == 0

    def test_empty_results(self, tmp_path: Path) -> None:
        """Should handle empty results gracefully."""
        empty_file = tmp_path / "empty.json"
        empty_file.write_text("{}")
        results = parse_playwright_results(empty_file)
        assert results.total == 0
        assert results.pass_rate == 0.0
