"""Screenshot capture and management for test failures."""

from __future__ import annotations

from pathlib import Path

from sharingan.config import SharinganConfig
from sharingan.run.parser import TestResult


def get_screenshot_path(test: TestResult, config: SharinganConfig) -> Path | None:
    """Get the screenshot path for a failing test.

    Args:
        test: The test result to get screenshot for.
        config: Sharingan configuration.

    Returns:
        Path to screenshot if it exists, None otherwise.
    """
    if test.screenshot_path:
        path = Path(test.screenshot_path)
        if path.exists():
            return path

    # Try to find screenshot by test name convention
    screenshots_dir = config.get_screenshots_path()
    if not screenshots_dir.exists():
        return None

    safe_name = test.name.replace(" ", "-").replace("/", "_")
    for ext in [".png", ".jpg", ".jpeg"]:
        candidate = screenshots_dir / f"{safe_name}{ext}"
        if candidate.exists():
            return candidate

    return None


def collect_screenshots(config: SharinganConfig) -> list[Path]:
    """Collect all screenshots from the screenshots directory.

    Args:
        config: Sharingan configuration.

    Returns:
        List of screenshot file paths.
    """
    screenshots_dir = config.get_screenshots_path()
    if not screenshots_dir.exists():
        return []

    screenshots: list[Path] = []
    for ext in ["*.png", "*.jpg", "*.jpeg"]:
        screenshots.extend(screenshots_dir.glob(ext))

    return sorted(screenshots)
