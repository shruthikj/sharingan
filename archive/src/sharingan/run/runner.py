"""Execute Playwright tests."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from sharingan.config import SharinganConfig


@dataclass
class RunResult:
    """Result of a Playwright test run."""

    exit_code: int
    stdout: str
    stderr: str
    results_path: Path | None = None
    duration_ms: int = 0


class PlaywrightRunner:
    """Execute Playwright tests and capture results."""

    def __init__(self, config: SharinganConfig) -> None:
        self.config = config

    def run_all(self, test_dir: Path | None = None) -> RunResult:
        """Run all Playwright tests in the given directory.

        Args:
            test_dir: Directory containing test files. Defaults to config test output dir.

        Returns:
            RunResult with exit code, output, and path to JSON results.
        """
        if test_dir is None:
            test_dir = self.config.get_test_output_path()

        results_path = test_dir / "results.json"
        screenshots_dir = self.config.get_screenshots_path()
        screenshots_dir.mkdir(parents=True, exist_ok=True)

        cmd = self._build_command(test_dir, results_path)
        return self._execute(cmd, results_path)

    def run_file(self, test_file: Path) -> RunResult:
        """Run a specific test file.

        Args:
            test_file: Path to the test file to run.

        Returns:
            RunResult with exit code, output, and path to JSON results.
        """
        results_path = test_file.parent / "results.json"
        cmd = self._build_command(test_file, results_path)
        return self._execute(cmd, results_path)

    def run_test(self, test_file: Path, test_name: str) -> RunResult:
        """Run a specific test by name within a file.

        Args:
            test_file: Path to the test file.
            test_name: Name of the test to run (grep pattern).

        Returns:
            RunResult with exit code and output.
        """
        results_path = test_file.parent / "results.json"
        cmd = self._build_command(test_file, results_path, grep=test_name)
        return self._execute(cmd, results_path)

    def _build_command(
        self,
        target: Path,
        results_path: Path,
        grep: str | None = None,
    ) -> list[str]:
        """Build the npx playwright test command."""
        cmd = [
            "npx", "playwright", "test",
            str(target),
            "--reporter=json",
            f"--output={results_path.parent}",
            f"--timeout={self.config.timeout_ms}",
        ]

        if self.config.headless:
            cmd.append("--headed=false")

        if grep:
            cmd.extend(["--grep", grep])

        if self.config.screenshot_on_failure:
            cmd.append("--screenshot=only-on-failure")

        return cmd

    def _execute(self, cmd: list[str], results_path: Path) -> RunResult:
        """Execute a command and return the result."""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.config.project_dir),
                timeout=self.config.timeout_ms * 2 / 1000,
            )

            # Try to write JSON results from stdout
            if result.stdout and results_path:
                try:
                    results_path.write_text(result.stdout)
                except OSError:
                    pass

            return RunResult(
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                results_path=results_path if results_path.exists() else None,
            )

        except subprocess.TimeoutExpired:
            return RunResult(
                exit_code=-1,
                stdout="",
                stderr="Test execution timed out",
            )
        except FileNotFoundError:
            return RunResult(
                exit_code=-1,
                stdout="",
                stderr="Playwright not found. Run: npm init playwright@latest",
            )
