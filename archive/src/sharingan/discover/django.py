"""Django URL discovery."""

from __future__ import annotations

import re
from pathlib import Path

from sharingan.discover.base import FrameworkDiscoverer, FrameworkInfo, RouteInfo


class DjangoDiscoverer(FrameworkDiscoverer):
    """Discover routes in a Django project."""

    def detect(self, project_dir: Path) -> FrameworkInfo | None:
        """Detect Django by checking for manage.py and django in requirements."""
        manage_py = project_dir / "manage.py"
        if not manage_py.exists():
            return None

        # Confirm django is in dependencies
        version = self._find_django_version(project_dir)
        if version is False:
            return None

        routes = self.discover_routes(project_dir)

        config_files = ["manage.py"]
        for name in ["settings.py", "urls.py"]:
            for found in project_dir.rglob(name):
                if "node_modules" not in found.parts and ".venv" not in found.parts:
                    config_files.append(str(found.relative_to(project_dir)))
                    break

        return FrameworkInfo(
            name="django",
            version=version if isinstance(version, str) else None,
            category="fullstack",
            routes=routes,
            config_files=config_files,
            root_dir=".",
        )

    def discover_routes(self, project_dir: Path) -> list[RouteInfo]:
        """Discover routes by parsing urls.py files."""
        routes: list[RouteInfo] = []

        for urls_file in project_dir.rglob("urls.py"):
            if ".venv" in urls_file.parts or "node_modules" in urls_file.parts:
                continue
            routes.extend(self._extract_urls(urls_file, project_dir))

        return routes

    def _extract_urls(self, file_path: Path, project_dir: Path) -> list[RouteInfo]:
        """Extract URL patterns from a Django urls.py file."""
        routes: list[RouteInfo] = []
        try:
            content = file_path.read_text(errors="replace")
        except OSError:
            return routes

        source_file = str(file_path.relative_to(project_dir))

        # Match: path('url/', view, name='...')
        path_pattern = re.compile(
            r"""path\s*\(\s*['"]([^'"]*)['"]\s*,""",
        )

        for match in path_pattern.finditer(content):
            url = "/" + match.group(1).strip("/")
            if url == "/":
                url = "/"

            context = content[match.start():match.start() + 300]
            has_auth = bool(re.search(r"login_required|permission_required|IsAuthenticated", context))

            dynamic_params = re.findall(r"<(?:\w+:)?(\w+)>", match.group(1))

            route_type = "api" if "api" in url.lower() else "page"

            routes.append(RouteInfo(
                path=url,
                route_type=route_type,
                has_auth=has_auth,
                source_file=source_file,
                dynamic_params=dynamic_params,
            ))

        return routes

    def _find_django_version(self, project_dir: Path) -> str | bool:
        """Find Django version from requirements."""
        for req_path in [
            project_dir / "requirements.txt",
            project_dir / "pyproject.toml",
        ]:
            if req_path.exists():
                content = req_path.read_text()
                if re.search(r"django", content, re.IGNORECASE):
                    match = re.search(r"[Dd]jango[=~><]*=*(\d+\.\d+(?:\.\d+)?)", content)
                    return match.group(1) if match else "unknown"

        # manage.py exists but no django in requirements — still likely Django
        manage_content = (project_dir / "manage.py").read_text(errors="replace")
        if "django" in manage_content.lower():
            return "unknown"

        return False
