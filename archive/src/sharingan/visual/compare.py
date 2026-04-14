"""Compare screenshots for visual regression."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class VisualDiffResult(BaseModel):
    """Result of a visual comparison."""

    test_name: str = Field(description="Name of the test")
    baseline_path: str = Field(description="Path to the baseline image")
    actual_path: str = Field(description="Path to the actual (new) image")
    diff_path: str = Field(default="", description="Path to the diff image if generated")
    diff_pixels: int = Field(default=0, description="Number of differing pixels")
    diff_ratio: float = Field(default=0.0, description="Ratio of differing pixels (0-1)")
    passed: bool = Field(description="Whether the visual test passed")
    message: str = Field(default="", description="Human-readable result message")


def format_diff_report(diff: VisualDiffResult) -> str:
    """Format a visual diff result as a markdown snippet.

    Args:
        diff: The visual diff result.

    Returns:
        Markdown snippet describing the diff.
    """
    status = "PASSED" if diff.passed else "FAILED"
    md = f"### {diff.test_name}: {status}\n\n"
    md += f"- **Diff pixels:** {diff.diff_pixels}\n"
    md += f"- **Diff ratio:** {diff.diff_ratio:.2%}\n"

    if diff.baseline_path and Path(diff.baseline_path).exists():
        md += f"- **Baseline:** `{diff.baseline_path}`\n"
    if diff.actual_path and Path(diff.actual_path).exists():
        md += f"- **Actual:** `{diff.actual_path}`\n"
    if diff.diff_path and Path(diff.diff_path).exists():
        md += f"- **Diff:** `{diff.diff_path}`\n"

    if diff.message:
        md += f"\n{diff.message}\n"

    return md
