"""React (CRA/Vite) route discovery."""

from __future__ import annotations

import json
import re
from pathlib import Path

from sharingan.discover.base import FrameworkDiscoverer, FrameworkInfo, RouteInfo


class ReactDiscoverer(FrameworkDiscoverer):
    """Discover routes in a React project (Create React App or Vite)."""

    def detect(self, project_dir: Path) -> FrameworkInfo | None:
        """Detect React by checking package.json dependencies."""
        package_json = self._find_package_json(project_dir)
        if package_json is None:
            return None

        data = json.loads(package_json.read_text())
        all_deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}

        # Skip if Next.js (handled by NextJSDiscoverer)
        if "next" in all_deps:
            return None

        if "react" not in all_deps:
            return None

        version = all_deps.get("react", "unknown")
        if version.startswith("^") or version.startswith("~"):
            version = version[1:]

        root_dir = str(package_json.parent.relative_to(project_dir))
        routes = self.discover_routes(package_json.parent)

        return FrameworkInfo(
            name="react",
            version=version,
            category="frontend",
            routes=routes,
            config_files=self._find_config_files(package_json.parent),
            root_dir=root_dir,
        )

    def discover_routes(self, project_dir: Path) -> list[RouteInfo]:
        """Discover routes by parsing React Router definitions."""
        routes: list[RouteInfo] = []

        src_dir = project_dir / "src"
        if not src_dir.is_dir():
            src_dir = project_dir

        for tsx_file in src_dir.rglob("*.tsx"):
            routes.extend(self._extract_routes_from_file(tsx_file, project_dir))
        for jsx_file in src_dir.rglob("*.jsx"):
            routes.extend(self._extract_routes_from_file(jsx_file, project_dir))

        if not routes:
            routes.append(RouteInfo(
                path="/",
                route_type="page",
                source_file="src/App.tsx",
            ))

        return routes

    def _extract_routes_from_file(self, file_path: Path, project_dir: Path) -> list[RouteInfo]:
        """Extract route definitions from a React file."""
        routes: list[RouteInfo] = []
        try:
            content = file_path.read_text(errors="replace")
        except OSError:
            return routes

        route_pattern = re.compile(
            r'<Route\s+[^>]*path\s*=\s*["\']([^"\']+)["\']',
            re.IGNORECASE,
        )

        source_file = str(file_path.relative_to(project_dir))
        for match in route_pattern.finditer(content):
            path = match.group(1)
            routes.append(RouteInfo(
                path=path,
                route_type="page",
                source_file=source_file,
                has_form=bool(re.search(r"<form[\s>]|onSubmit|handleSubmit", content)),
            ))

        return routes

    def _find_package_json(self, project_dir: Path) -> Path | None:
        """Find package.json."""
        for candidate in [
            project_dir / "package.json",
            project_dir / "frontend" / "package.json",
        ]:
            if candidate.exists():
                return candidate
        return None

    def _find_config_files(self, project_dir: Path) -> list[str]:
        """Find React-related config files."""
        config_files = []
        for name in ["vite.config.ts", "vite.config.js", "craco.config.js", "tsconfig.json"]:
            if (project_dir / name).exists():
                config_files.append(name)
        return config_files
