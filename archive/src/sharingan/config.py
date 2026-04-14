"""Sharingan configuration management."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class TestUserConfig(BaseModel):
    """Configuration for a test user used in authenticated flows."""

    email: str = Field(
        default="sharingan-test@example.local",
        description="Email for the test user (deterministic, single user reused across runs)",
    )
    password: str = Field(
        default="",
        description="Password for the test user. If empty, will auto-create or read from env.",
    )
    signup_route: str = Field(default="/signup", description="Route to sign up a new user")
    login_route: str = Field(default="/login", description="Route to log in")
    logout_route: str = Field(default="/logout", description="Route to log out")
    auto_create: bool = Field(
        default=True,
        description="Auto-create the test user via signup if login fails",
    )


class VisualConfig(BaseModel):
    """Configuration for visual regression testing."""

    enabled: bool = Field(default=True, description="Enable visual regression tests")
    threshold: float = Field(
        default=0.2,
        description="Pixel diff threshold (0-1). 0.2 = allow up to 20% difference",
    )
    max_diff_pixels: int = Field(default=100, description="Max number of diffing pixels allowed")
    baseline_dir: str = Field(
        default="tests/sharingan/visual-baselines",
        description="Directory where baseline screenshots are stored",
    )
    full_page: bool = Field(default=True, description="Capture full page screenshots")
    mask_dynamic: bool = Field(
        default=True,
        description="Mask dynamic content (timestamps, IDs) to avoid false positives",
    )


class PerfConfig(BaseModel):
    """Configuration for performance testing."""

    enabled: bool = Field(default=True, description="Enable performance tests")
    max_lcp_ms: int = Field(default=2500, description="Max Largest Contentful Paint in ms")
    max_fcp_ms: int = Field(default=1800, description="Max First Contentful Paint in ms")
    max_tti_ms: int = Field(default=3800, description="Max Time to Interactive in ms")
    max_total_size_kb: int = Field(default=2000, description="Max total page weight in KB")


class SchemaConfig(BaseModel):
    """Configuration for API schema validation."""

    enabled: bool = Field(default=True, description="Enable schema validation tests")
    openapi_paths: list[str] = Field(
        default_factory=lambda: ["/openapi.json", "/api/openapi.json", "/docs/openapi.json", "/api/v1/openapi.json"],
        description="Common paths to check for OpenAPI spec",
    )
    infer_from_samples: bool = Field(
        default=True,
        description="If no OpenAPI spec found, infer schema from first response and validate subsequent",
    )


class InterventionConfig(BaseModel):
    """Configuration for human-in-the-loop intervention."""

    enabled: bool = Field(default=True, description="Enable human-in-the-loop prompting")
    prompt_file: str = Field(
        default="SHARINGAN_NEEDS_HELP.md",
        description="File where Sharingan writes human intervention prompts",
    )
    pause_on_unknown: bool = Field(
        default=True,
        description="Pause and prompt for human help when test encounters unknown state",
    )
    timeout_seconds: int = Field(
        default=600,
        description="How long to wait for human to resolve intervention before marking as needs_review",
    )


class SharinganConfig(BaseModel):
    """Top-level configuration for a Sharingan run."""

    project_dir: Path = Field(default_factory=Path.cwd, description="Root directory of the target project")
    base_url: str = Field(default="http://localhost:3000", description="Base URL of the running application")
    api_base_url: str = Field(default="http://localhost:8000", description="Base URL of the API server")
    test_output_dir: str = Field(default="tests/sharingan", description="Directory for generated test files")
    max_fix_attempts: int = Field(default=3, description="Maximum fix attempts per failing test")
    max_iterations: int = Field(default=5, description="Maximum discover-test-fix loop iterations")
    timeout_ms: int = Field(default=30000, description="Default Playwright timeout in milliseconds")
    screenshot_on_failure: bool = Field(default=True, description="Capture screenshots on test failure")
    screenshot_every_step: bool = Field(
        default=True,
        description="Capture screenshots for every test, not just failures",
    )
    headless: bool = Field(default=True, description="Run browser in headless mode")
    browser: Literal["chromium", "firefox", "webkit"] = Field(default="chromium", description="Browser to use for tests")
    report_path: str = Field(default="SHARINGAN_REPORT.md", description="Path for the generated report")
    plan_path: str = Field(default="SHARINGAN_PLAN.md", description="Path for the generated test plan")
    frameworks: list[str] = Field(default_factory=list, description="Detected frameworks (auto-populated)")

    # Safety & prod guard
    allow_prod: bool = Field(default=False, description="Allow running against non-localhost URLs")

    # New v0.2 features
    test_user: TestUserConfig = Field(default_factory=TestUserConfig, description="Test user for auth flows")
    visual: VisualConfig = Field(default_factory=VisualConfig, description="Visual regression settings")
    perf: PerfConfig = Field(default_factory=PerfConfig, description="Performance testing settings")
    schema_validation: SchemaConfig = Field(default_factory=SchemaConfig, description="API schema validation settings")
    intervention: InterventionConfig = Field(
        default_factory=InterventionConfig,
        description="Human-in-the-loop intervention settings",
    )

    def get_test_output_path(self) -> Path:
        """Return the absolute path for test output."""
        return self.project_dir / self.test_output_dir

    def get_screenshots_path(self) -> Path:
        """Return the absolute path for screenshots."""
        return self.get_test_output_path() / "screenshots"

    def get_baseline_path(self) -> Path:
        """Return the absolute path for visual baselines."""
        return self.project_dir / self.visual.baseline_dir

    def get_credentials_path(self) -> Path:
        """Return the absolute path for gitignored credential storage."""
        return self.project_dir / ".sharingan" / "credentials.json"

    def get_report_path(self) -> Path:
        """Return the absolute path for the report."""
        return self.project_dir / self.report_path

    def get_plan_path(self) -> Path:
        """Return the absolute path for the test plan."""
        return self.project_dir / self.plan_path

    def get_intervention_prompt_path(self) -> Path:
        """Return the absolute path for the human intervention prompt file."""
        return self.project_dir / self.intervention.prompt_file

    def get_storage_state_path(self) -> Path:
        """Return the path for Playwright storage state (auth cookies/tokens)."""
        return self.get_test_output_path() / ".auth" / "storage-state.json"
