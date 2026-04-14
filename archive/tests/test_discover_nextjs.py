"""Tests for Next.js route discovery."""

from __future__ import annotations

from pathlib import Path

import pytest

from sharingan.discover.nextjs import NextJSDiscoverer


@pytest.fixture
def sample_nextjs_project(tmp_path: Path) -> Path:
    """Create a minimal Next.js project structure."""
    # package.json
    (tmp_path / "package.json").write_text('{"dependencies": {"next": "^14.2.0", "react": "^18.3.0"}}')
    (tmp_path / "next.config.js").write_text("module.exports = {};")

    # App directory
    app_dir = tmp_path / "src" / "app"
    app_dir.mkdir(parents=True)

    # Home page
    (app_dir / "page.tsx").write_text(
        'export default function Home() { return <h1>Home</h1>; }'
    )

    # Layout
    (app_dir / "layout.tsx").write_text(
        'export default function Layout({ children }) { return <html><body>{children}</body></html>; }'
    )

    # Login page with form
    login_dir = app_dir / "login"
    login_dir.mkdir()
    (login_dir / "page.tsx").write_text(
        '"use client";\nexport default function Login() { return <form onSubmit={handleSubmit}><input /><button>Login</button></form>; }'
    )

    # Dashboard (auth-protected)
    dash_dir = app_dir / "dashboard"
    dash_dir.mkdir()
    (dash_dir / "page.tsx").write_text(
        '"use client";\nimport { useSession } from "next-auth";\nexport default function Dashboard() { return <h1>Dashboard</h1>; }'
    )

    # API route
    api_dir = app_dir / "api" / "health"
    api_dir.mkdir(parents=True)
    (api_dir / "route.ts").write_text(
        'export async function GET() { return Response.json({ status: "ok" }); }'
    )

    # Dynamic route
    user_dir = app_dir / "users" / "[id]"
    user_dir.mkdir(parents=True)
    (user_dir / "page.tsx").write_text(
        'export default function UserPage({ params }) { return <h1>User {params.id}</h1>; }'
    )

    return tmp_path


class TestNextJSDiscoverer:
    """Tests for NextJSDiscoverer."""

    def test_detect_nextjs_project(self, sample_nextjs_project: Path) -> None:
        """Should detect a Next.js project from package.json."""
        discoverer = NextJSDiscoverer()
        result = discoverer.detect(sample_nextjs_project)

        assert result is not None
        assert result.name == "nextjs"
        assert result.version == "14.2.0"
        assert result.category == "fullstack"
        assert "next.config.js" in result.config_files

    def test_detect_non_nextjs_project(self, tmp_path: Path) -> None:
        """Should return None for non-Next.js projects."""
        (tmp_path / "package.json").write_text('{"dependencies": {"express": "^4.0.0"}}')
        discoverer = NextJSDiscoverer()
        result = discoverer.detect(tmp_path)
        assert result is None

    def test_detect_no_package_json(self, tmp_path: Path) -> None:
        """Should return None when no package.json exists."""
        discoverer = NextJSDiscoverer()
        result = discoverer.detect(tmp_path)
        assert result is None

    def test_discover_page_routes(self, sample_nextjs_project: Path) -> None:
        """Should discover page routes from app directory."""
        discoverer = NextJSDiscoverer()
        result = discoverer.detect(sample_nextjs_project)
        assert result is not None

        page_routes = [r for r in result.routes if r.route_type == "page"]
        paths = {r.path for r in page_routes}

        assert "/" in paths
        assert "/login" in paths

    def test_discover_form_pages(self, sample_nextjs_project: Path) -> None:
        """Should detect pages with forms."""
        discoverer = NextJSDiscoverer()
        result = discoverer.detect(sample_nextjs_project)
        assert result is not None

        login_routes = [r for r in result.routes if r.path == "/login"]
        assert len(login_routes) == 1
        assert login_routes[0].has_form is True

    def test_discover_auth_protected_pages(self, sample_nextjs_project: Path) -> None:
        """Should detect auth-protected pages."""
        discoverer = NextJSDiscoverer()
        result = discoverer.detect(sample_nextjs_project)
        assert result is not None

        dashboard_routes = [r for r in result.routes if r.path == "/dashboard"]
        assert len(dashboard_routes) == 1
        assert dashboard_routes[0].has_auth is True

    def test_discover_api_routes(self, sample_nextjs_project: Path) -> None:
        """Should discover API routes."""
        discoverer = NextJSDiscoverer()
        result = discoverer.detect(sample_nextjs_project)
        assert result is not None

        api_routes = [r for r in result.routes if r.route_type == "api"]
        assert len(api_routes) >= 1
        assert any("/api/health" in r.path for r in api_routes)

    def test_discover_dynamic_routes(self, sample_nextjs_project: Path) -> None:
        """Should discover dynamic routes with parameters."""
        discoverer = NextJSDiscoverer()
        result = discoverer.detect(sample_nextjs_project)
        assert result is not None

        dynamic_routes = [r for r in result.routes if r.route_type == "dynamic"]
        assert len(dynamic_routes) >= 1
        assert any("id" in r.dynamic_params for r in dynamic_routes)

    def test_discover_layout(self, sample_nextjs_project: Path) -> None:
        """Should discover layout files."""
        discoverer = NextJSDiscoverer()
        result = discoverer.detect(sample_nextjs_project)
        assert result is not None

        layouts = [r for r in result.routes if r.route_type == "layout"]
        assert len(layouts) >= 1

    def test_nested_in_frontend_dir(self, tmp_path: Path) -> None:
        """Should detect Next.js in a frontend/ subdirectory."""
        frontend = tmp_path / "frontend"
        frontend.mkdir()
        (frontend / "package.json").write_text('{"dependencies": {"next": "^14.0.0"}}')
        app_dir = frontend / "src" / "app"
        app_dir.mkdir(parents=True)
        (app_dir / "page.tsx").write_text("<h1>Hello</h1>")

        discoverer = NextJSDiscoverer()
        result = discoverer.detect(tmp_path)
        assert result is not None
        assert result.name == "nextjs"
