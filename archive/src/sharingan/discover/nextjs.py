"""Next.js App Router route discovery."""

from __future__ import annotations

import json
import re
from pathlib import Path

from sharingan.discover.base import FrameworkDiscoverer, FrameworkInfo, RouteInfo


class NextJSDiscoverer(FrameworkDiscoverer):
    """Discover routes in a Next.js App Router project."""

    def detect(self, project_dir: Path) -> FrameworkInfo | None:
        """Detect Next.js by checking package.json for 'next' dependency."""
        package_json = self._find_package_json(project_dir)
        if package_json is None:
            return None

        data = json.loads(package_json.read_text())
        all_deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}

        if "next" not in all_deps:
            return None

        version = all_deps.get("next", "unknown")
        if version.startswith("^") or version.startswith("~"):
            version = version[1:]

        root_dir = str(package_json.parent.relative_to(project_dir))

        routes = self.discover_routes(package_json.parent)

        config_files = []
        for name in ["next.config.js", "next.config.mjs", "next.config.ts"]:
            if (package_json.parent / name).exists():
                config_files.append(name)

        return FrameworkInfo(
            name="nextjs",
            version=version,
            category="fullstack",
            routes=routes,
            config_files=config_files,
            root_dir=root_dir,
        )

    def discover_routes(self, project_dir: Path) -> list[RouteInfo]:
        """Discover routes from the App Router directory structure."""
        routes: list[RouteInfo] = []

        app_dir = self._find_app_dir(project_dir)
        if app_dir is None:
            return routes

        self._scan_directory(app_dir, app_dir, routes, project_dir)
        return routes

    def _find_package_json(self, project_dir: Path) -> Path | None:
        """Find package.json, checking common locations."""
        for candidate in [
            project_dir / "package.json",
            project_dir / "frontend" / "package.json",
        ]:
            if candidate.exists():
                return candidate
        return None

    def _find_app_dir(self, project_dir: Path) -> Path | None:
        """Find the Next.js app directory."""
        for candidate in [
            project_dir / "src" / "app",
            project_dir / "app",
        ]:
            if candidate.is_dir():
                return candidate
        return None

    def _scan_directory(
        self, current: Path, app_root: Path, routes: list[RouteInfo], project_dir: Path
    ) -> None:
        """Recursively scan directory for route files."""
        if not current.is_dir():
            return

        rel_path = current.relative_to(app_root)
        parts = list(rel_path.parts)
        url_segments = [self._segment_to_url(part) for part in parts]
        url_path = "/" + "/".join(seg for seg in url_segments if seg)
        if url_path == "/.":
            url_path = "/"

        for child in sorted(current.iterdir()):
            if child.is_file():
                route = self._process_file(child, url_path, app_root, project_dir)
                if route is not None:
                    routes.append(route)
            elif child.is_dir() and not child.name.startswith(("_", ".")):
                self._scan_directory(child, app_root, routes, project_dir)

    def _process_file(
        self, file_path: Path, url_path: str, app_root: Path, project_dir: Path
    ) -> RouteInfo | None:
        """Process a single file to extract route info."""
        name = file_path.stem
        suffix = file_path.suffix

        if suffix not in (".tsx", ".ts", ".jsx", ".js"):
            return None

        source_file = str(file_path.relative_to(project_dir))

        if name == "page":
            content = file_path.read_text(errors="replace")
            has_form = bool(re.search(r"<form[\s>]|onSubmit|handleSubmit", content))
            has_auth = bool(re.search(r"useSession|getServerSession|auth|protect", content, re.IGNORECASE))
            # Extract dynamic params from directory names (e.g. [id], [...slug])
            dir_path = str(file_path.parent.relative_to(app_root))
            dynamic_params = re.findall(r"\[(\w+)\]", dir_path)

            route_type = "dynamic" if dynamic_params else "page"

            return RouteInfo(
                path=url_path,
                method="GET",
                route_type=route_type,
                has_auth=has_auth,
                has_form=has_form,
                source_file=source_file,
                dynamic_params=dynamic_params,
            )

        if name == "route":
            content = file_path.read_text(errors="replace")
            api_path = url_path if url_path.startswith("/api") else url_path

            methods_found = []
            for method in ["GET", "POST", "PUT", "PATCH", "DELETE"]:
                if re.search(rf"export\s+(async\s+)?function\s+{method}\b", content):
                    methods_found.append(method)

            if not methods_found:
                methods_found = ["GET"]

            routes = []
            for method in methods_found:
                routes.append(RouteInfo(
                    path=api_path,
                    method=method,
                    route_type="api",
                    has_auth=bool(re.search(r"auth|token|session", content, re.IGNORECASE)),
                    source_file=source_file,
                ))
            # Return only the first; caller should handle multiple methods
            return routes[0] if routes else None

        if name == "layout":
            return RouteInfo(
                path=url_path,
                route_type="layout",
                source_file=source_file,
            )

        if name == "middleware":
            content = file_path.read_text(errors="replace")
            return RouteInfo(
                path=url_path,
                route_type="middleware",
                has_auth=bool(re.search(r"auth|token|session|protect", content, re.IGNORECASE)),
                source_file=source_file,
            )

        return None

    def _segment_to_url(self, segment: str) -> str:
        """Convert directory segment to URL segment."""
        if segment.startswith("[") and segment.endswith("]"):
            return f":{segment[1:-1]}"
        if segment.startswith("(") and segment.endswith(")"):
            return ""
        return segment
