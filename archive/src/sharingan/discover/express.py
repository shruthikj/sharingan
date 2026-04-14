"""Express.js route discovery."""

from __future__ import annotations

import json
import re
from pathlib import Path

from sharingan.discover.base import FrameworkDiscoverer, FrameworkInfo, RouteInfo


class ExpressDiscoverer(FrameworkDiscoverer):
    """Discover routes in an Express.js project."""

    def detect(self, project_dir: Path) -> FrameworkInfo | None:
        """Detect Express by checking package.json for 'express' dependency."""
        package_json = self._find_package_json(project_dir)
        if package_json is None:
            return None

        data = json.loads(package_json.read_text())
        all_deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}

        if "express" not in all_deps:
            return None

        version = all_deps.get("express", "unknown")
        if version.startswith("^") or version.startswith("~"):
            version = version[1:]

        root_dir = str(package_json.parent.relative_to(project_dir))
        routes = self.discover_routes(package_json.parent)

        return FrameworkInfo(
            name="express",
            version=version,
            category="backend",
            routes=routes,
            config_files=["package.json"],
            root_dir=root_dir,
        )

    def discover_routes(self, project_dir: Path) -> list[RouteInfo]:
        """Discover routes by scanning JS/TS files for Express route definitions."""
        routes: list[RouteInfo] = []

        for pattern in ["**/*.js", "**/*.ts"]:
            for js_file in project_dir.glob(pattern):
                if "node_modules" in js_file.parts:
                    continue
                routes.extend(self._extract_routes(js_file, project_dir))

        return routes

    def _extract_routes(self, file_path: Path, project_dir: Path) -> list[RouteInfo]:
        """Extract Express route definitions from a file."""
        routes: list[RouteInfo] = []
        try:
            content = file_path.read_text(errors="replace")
        except OSError:
            return routes

        source_file = str(file_path.relative_to(project_dir))

        # Match: app.get('/path', ...), router.post('/path', ...)
        route_pattern = re.compile(
            r'(?:app|router)\.(get|post|put|patch|delete)\s*\(\s*["\']([^"\']+)["\']',
            re.IGNORECASE,
        )

        for match in route_pattern.finditer(content):
            method = match.group(1).upper()
            path = match.group(2)

            # Check for auth middleware
            func_context = content[match.start():match.start() + 300]
            has_auth = bool(re.search(r"auth|protect|verify|isAuthenticated", func_context, re.IGNORECASE))

            dynamic_params = re.findall(r":(\w+)", path)

            routes.append(RouteInfo(
                path=path,
                method=method,
                route_type="api",
                has_auth=has_auth,
                source_file=source_file,
                dynamic_params=dynamic_params,
            ))

        return routes

    def _find_package_json(self, project_dir: Path) -> Path | None:
        """Find package.json."""
        for candidate in [
            project_dir / "package.json",
            project_dir / "backend" / "package.json",
            project_dir / "server" / "package.json",
        ]:
            if candidate.exists():
                return candidate
        return None
