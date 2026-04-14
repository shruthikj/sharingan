"""FastAPI endpoint discovery."""

from __future__ import annotations

import re
from pathlib import Path

from sharingan.discover.base import FrameworkDiscoverer, FrameworkInfo, RouteInfo


class FastAPIDiscoverer(FrameworkDiscoverer):
    """Discover endpoints in a FastAPI project."""

    def detect(self, project_dir: Path) -> FrameworkInfo | None:
        """Detect FastAPI by checking requirements or pyproject.toml."""
        req_file = self._find_requirements(project_dir)
        if req_file is None:
            return None

        content = req_file.read_text()
        if not re.search(r"fastapi", content, re.IGNORECASE):
            return None

        version_match = re.search(r"fastapi[=~><]*=*(\d+\.\d+(?:\.\d+)?)", content, re.IGNORECASE)
        version = version_match.group(1) if version_match else None

        root_dir = str(req_file.parent.relative_to(project_dir))
        routes = self.discover_routes(req_file.parent)

        return FrameworkInfo(
            name="fastapi",
            version=version,
            category="backend",
            routes=routes,
            config_files=[req_file.name],
            root_dir=root_dir,
        )

    def discover_routes(self, project_dir: Path) -> list[RouteInfo]:
        """Discover all FastAPI endpoints by scanning Python files."""
        routes: list[RouteInfo] = []

        for py_file in project_dir.rglob("*.py"):
            if py_file.name.startswith("_") and py_file.name != "__init__.py":
                continue
            routes.extend(self._extract_endpoints(py_file, project_dir))

        return routes

    def _extract_endpoints(self, file_path: Path, project_dir: Path) -> list[RouteInfo]:
        """Extract FastAPI endpoint definitions from a Python file."""
        routes: list[RouteInfo] = []
        try:
            content = file_path.read_text(errors="replace")
        except OSError:
            return routes

        # Check if file imports or uses FastAPI
        if not re.search(r"fastapi|FastAPI|APIRouter", content):
            return routes

        source_file = str(file_path.relative_to(project_dir))

        # Match decorator patterns: @app.get("/path"), @router.post("/path")
        endpoint_pattern = re.compile(
            r'@(?:\w+)\.(get|post|put|patch|delete|options|head)\s*\(\s*["\']([^"\']+)["\']',
            re.IGNORECASE,
        )

        for match in endpoint_pattern.finditer(content):
            method = match.group(1).upper()
            path = match.group(2)

            # Check for auth dependencies
            # Look at the function following this decorator
            func_start = match.end()
            func_block = content[func_start:func_start + 500]
            has_auth = bool(re.search(
                r"Depends\s*\(\s*(?:get_current_user|auth|verify_token|require_auth)",
                func_block,
                re.IGNORECASE,
            ))

            # Check for request body (indicates form/input)
            has_form = bool(re.search(r"Body\s*\(|BaseModel|Schema", func_block))

            dynamic_params = re.findall(r"\{(\w+)\}", path)

            routes.append(RouteInfo(
                path=path,
                method=method,
                route_type="api",
                has_auth=has_auth,
                has_form=has_form,
                source_file=source_file,
                dynamic_params=dynamic_params,
            ))

        return routes

    def _find_requirements(self, project_dir: Path) -> Path | None:
        """Find requirements file, checking common locations."""
        for candidate in [
            project_dir / "requirements.txt",
            project_dir / "backend" / "requirements.txt",
            project_dir / "pyproject.toml",
        ]:
            if candidate.exists():
                return candidate
        return None
