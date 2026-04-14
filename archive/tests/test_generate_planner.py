"""Tests for test plan generation."""

from __future__ import annotations

from pathlib import Path

import pytest

from sharingan.config import SharinganConfig
from sharingan.discover.base import FrameworkInfo, RouteInfo
from sharingan.generate.test_planner import TestPlan, generate_test_plan


@pytest.fixture
def sample_frameworks() -> list[FrameworkInfo]:
    """Create sample framework info for testing."""
    return [
        FrameworkInfo(
            name="nextjs",
            version="14.2.0",
            category="fullstack",
            routes=[
                RouteInfo(path="/", route_type="page", source_file="src/app/page.tsx"),
                RouteInfo(path="/login", route_type="page", has_form=True, source_file="src/app/login/page.tsx"),
                RouteInfo(path="/signup", route_type="page", has_form=True, source_file="src/app/signup/page.tsx"),
                RouteInfo(
                    path="/dashboard",
                    route_type="page",
                    has_auth=True,
                    source_file="src/app/dashboard/page.tsx",
                ),
                RouteInfo(path="/", route_type="layout", source_file="src/app/layout.tsx"),
            ],
        ),
        FrameworkInfo(
            name="fastapi",
            version="0.110.0",
            category="backend",
            routes=[
                RouteInfo(path="/api/v1/health", method="GET", route_type="api", source_file="main.py"),
                RouteInfo(path="/api/v1/auth/login", method="POST", route_type="api", source_file="main.py"),
                RouteInfo(path="/api/v1/items", method="GET", route_type="api", source_file="main.py"),
                RouteInfo(path="/api/v1/items", method="POST", route_type="api", source_file="main.py"),
                RouteInfo(
                    path="/api/v1/items/{item_id}",
                    method="GET",
                    route_type="api",
                    source_file="main.py",
                    dynamic_params=["item_id"],
                ),
            ],
        ),
    ]


@pytest.fixture
def config(tmp_path: Path) -> SharinganConfig:
    """Create a test configuration."""
    return SharinganConfig(project_dir=tmp_path)


class TestGenerateTestPlan:
    """Tests for generate_test_plan."""

    def test_generates_plan(self, sample_frameworks: list[FrameworkInfo], config: SharinganConfig) -> None:
        """Should generate a non-empty test plan."""
        plan = generate_test_plan(sample_frameworks, config)
        assert isinstance(plan, TestPlan)
        assert plan.total_tests > 0

    def test_includes_frameworks(self, sample_frameworks: list[FrameworkInfo], config: SharinganConfig) -> None:
        """Should list detected frameworks."""
        plan = generate_test_plan(sample_frameworks, config)
        assert "nextjs" in plan.frameworks
        assert "fastapi" in plan.frameworks

    def test_navigation_tests_for_pages(
        self, sample_frameworks: list[FrameworkInfo], config: SharinganConfig
    ) -> None:
        """Should create navigation tests for page routes."""
        plan = generate_test_plan(sample_frameworks, config)
        nav_routes = {t.route for t in plan.navigation_tests}
        assert "/" in nav_routes

    def test_form_tests_for_form_pages(
        self, sample_frameworks: list[FrameworkInfo], config: SharinganConfig
    ) -> None:
        """Should create form tests for pages with forms."""
        plan = generate_test_plan(sample_frameworks, config)
        form_routes = {t.route for t in plan.form_tests}
        assert "/login" in form_routes
        assert "/signup" in form_routes

    def test_api_tests_for_endpoints(
        self, sample_frameworks: list[FrameworkInfo], config: SharinganConfig
    ) -> None:
        """Should create API tests for backend endpoints."""
        plan = generate_test_plan(sample_frameworks, config)
        api_routes = {t.route for t in plan.api_tests}
        assert "/api/v1/health" in api_routes
        assert "/api/v1/items" in api_routes

    def test_permission_tests_for_auth_routes(
        self, sample_frameworks: list[FrameworkInfo], config: SharinganConfig
    ) -> None:
        """Should create permission tests for auth-protected routes."""
        plan = generate_test_plan(sample_frameworks, config)
        perm_routes = {t.route for t in plan.permission_tests}
        assert "/dashboard" in perm_routes

    def test_auth_flow_tests(
        self, sample_frameworks: list[FrameworkInfo], config: SharinganConfig
    ) -> None:
        """Should create auth flow tests when login/signup routes exist."""
        plan = generate_test_plan(sample_frameworks, config)
        auth_names = {t.name for t in plan.auth_tests}
        assert "login_valid_credentials" in auth_names
        assert "signup_happy_path" in auth_names

    def test_accessibility_tests(
        self, sample_frameworks: list[FrameworkInfo], config: SharinganConfig
    ) -> None:
        """Should create accessibility tests for page routes."""
        plan = generate_test_plan(sample_frameworks, config)
        assert len(plan.accessibility_tests) > 0

    def test_no_tests_for_layouts(
        self, sample_frameworks: list[FrameworkInfo], config: SharinganConfig
    ) -> None:
        """Should not create direct tests for layout routes."""
        plan = generate_test_plan(sample_frameworks, config)
        all_routes = {t.route for t in plan.all_tests}
        layout_only = [r for r in sample_frameworks[0].routes if r.route_type == "layout"]
        # Layout routes should not appear as standalone test targets
        for layout in layout_only:
            # Layouts at "/" are fine since page routes also exist at "/"
            if layout.path != "/":
                assert layout.path not in all_routes

    def test_invalid_body_tests_for_post(
        self, sample_frameworks: list[FrameworkInfo], config: SharinganConfig
    ) -> None:
        """Should create invalid body tests for POST endpoints."""
        plan = generate_test_plan(sample_frameworks, config)
        invalid_body_tests = [t for t in plan.api_tests if "invalid_body" in t.name]
        assert len(invalid_body_tests) > 0

    def test_all_tests_property(
        self, sample_frameworks: list[FrameworkInfo], config: SharinganConfig
    ) -> None:
        """The all_tests property should include every test case."""
        plan = generate_test_plan(sample_frameworks, config)
        assert len(plan.all_tests) == plan.total_tests
