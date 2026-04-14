"""Re-run failing tests to verify fixes."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from sharingan.config import SharinganConfig
from sharingan.fix.fixer import FixResult
from sharingan.run.runner import PlaywrightRunner


class ValidationResult(BaseModel):
    """Result of fix validation."""

    test_name: str = Field(description="Name of the test being validated")
    fix_verified: bool = Field(description="Whether the fix resolved the failure")
    attempt: int = Field(default=1, description="Which attempt this was")
    new_error: str = Field(default="", description="New error if the test still fails")


def validate_fix(
    fix_result: FixResult,
    test_file: Path,
    test_name: str,
    config: SharinganConfig,
) -> ValidationResult:
    """Re-run a specific test to verify that a fix resolved the failure.

    Args:
        fix_result: The applied fix result.
        test_file: Path to the test file.
        test_name: Name of the specific test to re-run.
        config: Sharingan configuration.

    Returns:
        ValidationResult indicating whether the fix worked.
    """
    if not fix_result.success:
        return ValidationResult(
            test_name=test_name,
            fix_verified=False,
            new_error="Fix was not applied successfully",
        )

    runner = PlaywrightRunner(config)
    result = runner.run_test(test_file, test_name)

    if result.exit_code == 0:
        return ValidationResult(
            test_name=test_name,
            fix_verified=True,
        )

    return ValidationResult(
        test_name=test_name,
        fix_verified=False,
        new_error=result.stderr[:500] if result.stderr else "Test still failing",
    )
