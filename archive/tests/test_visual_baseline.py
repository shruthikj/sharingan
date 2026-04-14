"""Tests for the visual regression module."""

from __future__ import annotations

from pathlib import Path

from sharingan.config import SharinganConfig
from sharingan.visual.baseline import BaselineManager
from sharingan.visual.compare import VisualDiffResult, format_diff_report


class TestBaselineManager:
    """Tests for BaselineManager."""

    def test_ensure_baseline_dir(self, tmp_path: Path) -> None:
        """Should create the baseline directory."""
        config = SharinganConfig(project_dir=tmp_path)
        manager = BaselineManager(config)
        manager.ensure_baseline_dir()
        assert manager.baseline_dir.exists()

    def test_has_baseline_false_initially(self, tmp_path: Path) -> None:
        """Should return False when no baseline exists."""
        config = SharinganConfig(project_dir=tmp_path)
        manager = BaselineManager(config)
        assert manager.has_baseline("home_page") is False

    def test_has_baseline_after_creation(self, tmp_path: Path) -> None:
        """Should return True after baseline exists."""
        config = SharinganConfig(project_dir=tmp_path)
        manager = BaselineManager(config)
        manager.ensure_baseline_dir()

        baseline_path = manager.get_baseline_path("home_page")
        baseline_path.write_bytes(b"fake png data")

        assert manager.has_baseline("home_page") is True

    def test_list_baselines_empty(self, tmp_path: Path) -> None:
        """Should return empty list when no baselines exist."""
        config = SharinganConfig(project_dir=tmp_path)
        manager = BaselineManager(config)
        assert manager.list_baselines() == []

    def test_list_baselines_with_files(self, tmp_path: Path) -> None:
        """Should list all PNG files in baseline dir."""
        config = SharinganConfig(project_dir=tmp_path)
        manager = BaselineManager(config)
        manager.ensure_baseline_dir()

        (manager.baseline_dir / "test1.png").write_bytes(b"png1")
        (manager.baseline_dir / "test2.png").write_bytes(b"png2")

        baselines = manager.list_baselines()
        assert len(baselines) == 2

    def test_safe_name_converts_special_chars(self, tmp_path: Path) -> None:
        """Should convert test names with spaces and slashes to safe filenames."""
        config = SharinganConfig(project_dir=tmp_path)
        manager = BaselineManager(config)
        path = manager.get_baseline_path("Home / Landing Page")
        assert " " not in path.name
        assert "/" not in path.stem


class TestFormatDiffReport:
    """Tests for format_diff_report."""

    def test_passed_report(self) -> None:
        """Should format a passed diff nicely."""
        diff = VisualDiffResult(
            test_name="home_page",
            baseline_path="baselines/home.png",
            actual_path="actual/home.png",
            diff_pixels=10,
            diff_ratio=0.001,
            passed=True,
        )
        report = format_diff_report(diff)
        assert "PASSED" in report
        assert "home_page" in report

    def test_failed_report_shows_details(self) -> None:
        """Should show diff details for failed tests."""
        diff = VisualDiffResult(
            test_name="checkout",
            baseline_path="/path/to/baseline.png",
            actual_path="/path/to/actual.png",
            diff_pixels=5000,
            diff_ratio=0.25,
            passed=False,
            message="Significant visual change detected",
        )
        report = format_diff_report(diff)
        assert "FAILED" in report
        assert "5000" in report
        assert "25" in report  # ratio rendered
