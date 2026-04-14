"""Analyze test failures to determine root cause."""

from __future__ import annotations

import re
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field

from sharingan.run.parser import TestResult


class DiagnosisType(str, Enum):
    """Type of failure diagnosis."""

    TEST_BUG = "test_bug"
    APP_BUG = "app_bug"
    CONFIG_ISSUE = "config_issue"
    UNKNOWN = "unknown"


class Diagnosis(BaseModel):
    """Diagnosis of a test failure."""

    test_name: str = Field(description="Name of the failing test")
    diagnosis_type: DiagnosisType = Field(description="Type of failure")
    confidence: float = Field(default=0.5, description="Confidence in diagnosis (0-1)")
    summary: str = Field(description="Human-readable summary of the diagnosis")
    suggested_file: str = Field(default="", description="File that likely needs to be fixed")
    suggested_fix: str = Field(default="", description="Description of the suggested fix")
    error_pattern: str = Field(default="", description="Matched error pattern")


# Error patterns that indicate test bugs vs app bugs
TEST_BUG_PATTERNS = [
    (r"locator\..*resolved to \d+ elements", "Ambiguous locator — multiple elements matched"),
    (r"waiting for locator", "Element not found — wrong selector or timing issue"),
    (r"strict mode violation", "Strict mode: multiple elements match the locator"),
    (r"Target closed", "Browser closed unexpectedly — possible race condition in test"),
    (r"timeout \d+ms exceeded.*waiting", "Timeout waiting for element — test timing issue"),
    (r"Expected .* to have URL", "URL assertion failed — navigation timing or wrong expected URL"),
]

APP_BUG_PATTERNS = [
    (r"status (?:500|502|503)", "Server error — application bug"),
    (r"net::ERR_CONNECTION_REFUSED", "Application not running or port mismatch"),
    (r"404 Not Found", "Route not found — missing page or API endpoint"),
    (r"403 Forbidden", "Access denied — possible auth/permission bug"),
    (r"TypeError.*(?:undefined|null)", "Runtime error — null/undefined reference in application"),
    (r"Unhandled Runtime Error", "Unhandled error in application"),
    (r"Internal Server Error", "Server-side error in application"),
    (r"CORS.*blocked", "CORS configuration issue"),
    (r"422 Unprocessable", "Validation error — missing or invalid request handling"),
]


def analyze_failure(test: TestResult, project_dir: Path | None = None) -> Diagnosis:
    """Analyze a test failure and diagnose the root cause.

    Examines the error message and code context to determine whether
    the failure is caused by a test bug (wrong selector, timing) or
    an application bug (broken route, logic error).

    Args:
        test: The failing test result.
        project_dir: Root directory of the project (for source reading).

    Returns:
        Diagnosis with type, confidence, and suggested fix.
    """
    error = test.error_message.lower()

    # Check test bug patterns
    for pattern, description in TEST_BUG_PATTERNS:
        if re.search(pattern, test.error_message, re.IGNORECASE):
            return Diagnosis(
                test_name=test.name,
                diagnosis_type=DiagnosisType.TEST_BUG,
                confidence=0.8,
                summary=f"Test bug: {description}",
                suggested_file=test.file_path,
                suggested_fix=f"Fix the test: {description}",
                error_pattern=pattern,
            )

    # Check app bug patterns
    for pattern, description in APP_BUG_PATTERNS:
        if re.search(pattern, test.error_message, re.IGNORECASE):
            suggested_file = _guess_source_file(test, project_dir) if project_dir else ""
            return Diagnosis(
                test_name=test.name,
                diagnosis_type=DiagnosisType.APP_BUG,
                confidence=0.8,
                summary=f"Application bug: {description}",
                suggested_file=suggested_file,
                suggested_fix=f"Fix the application: {description}",
                error_pattern=pattern,
            )

    # Check for configuration issues
    if any(kw in error for kw in ["enoent", "module not found", "cannot find", "no such file"]):
        return Diagnosis(
            test_name=test.name,
            diagnosis_type=DiagnosisType.CONFIG_ISSUE,
            confidence=0.7,
            summary="Configuration issue: missing file or module",
            suggested_fix="Check project configuration and dependencies",
        )

    # Default: unknown
    return Diagnosis(
        test_name=test.name,
        diagnosis_type=DiagnosisType.UNKNOWN,
        confidence=0.3,
        summary=f"Unknown failure: {test.error_message[:200]}",
        suggested_file=test.file_path,
        suggested_fix="Manual investigation needed",
    )


def _guess_source_file(test: TestResult, project_dir: Path) -> str:
    """Try to guess which source file corresponds to a failing test."""
    # Extract route from test name
    route_match = re.search(r"(/[\w/-]+)", test.name)
    if not route_match:
        return ""

    route = route_match.group(1)

    # Try common Next.js patterns
    candidates = [
        project_dir / "src" / "app" / route.strip("/") / "page.tsx",
        project_dir / "src" / "app" / route.strip("/") / "page.jsx",
        project_dir / "app" / route.strip("/") / "page.tsx",
    ]

    for candidate in candidates:
        if candidate.exists():
            return str(candidate.relative_to(project_dir))

    return ""
