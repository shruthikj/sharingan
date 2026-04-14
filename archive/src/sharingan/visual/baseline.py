"""Manage visual regression baseline screenshots."""

from __future__ import annotations

from pathlib import Path

from sharingan.config import SharinganConfig


class BaselineManager:
    """Manages baseline screenshots for visual regression tests.

    Baselines are captured on the first run and stored in
    tests/sharingan/visual-baselines/. Subsequent runs compare against
    these baselines using Playwright's built-in toHaveScreenshot().
    """

    def __init__(self, config: SharinganConfig) -> None:
        self.config = config
        self.baseline_dir = config.get_baseline_path()

    def ensure_baseline_dir(self) -> None:
        """Create the baseline directory if it doesn't exist."""
        self.baseline_dir.mkdir(parents=True, exist_ok=True)

    def has_baseline(self, test_name: str) -> bool:
        """Check if a baseline exists for a given test.

        Args:
            test_name: Name of the test (used as filename stem).

        Returns:
            True if a baseline PNG exists.
        """
        baseline_file = self.baseline_dir / f"{self._safe_name(test_name)}.png"
        return baseline_file.exists()

    def get_baseline_path(self, test_name: str) -> Path:
        """Get the path where a baseline should be stored.

        Args:
            test_name: Name of the test.

        Returns:
            Absolute path to the baseline file.
        """
        return self.baseline_dir / f"{self._safe_name(test_name)}.png"

    def list_baselines(self) -> list[Path]:
        """Return all existing baseline files."""
        if not self.baseline_dir.exists():
            return []
        return sorted(self.baseline_dir.glob("*.png"))

    def _safe_name(self, test_name: str) -> str:
        """Convert test name to a filesystem-safe identifier."""
        return test_name.replace(" ", "-").replace("/", "_").lower()
