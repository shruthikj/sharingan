"""Tests for framework auto-detection."""

from __future__ import annotations

from pathlib import Path

import pytest

from sharingan.discover.detector import detect_frameworks


@pytest.fixture
def fullstack_project(tmp_path: Path) -> Path:
    """Create a project with both Next.js frontend and FastAPI backend."""
    # Frontend
    frontend = tmp_path / "frontend"
    frontend.mkdir()
    (frontend / "package.json").write_text('{"dependencies": {"next": "^14.2.0", "react": "^18.3.0"}}')
    app_dir = frontend / "src" / "app"
    app_dir.mkdir(parents=True)
    (app_dir / "page.tsx").write_text("<h1>Home</h1>")
    login_dir = app_dir / "login"
    login_dir.mkdir()
    (login_dir / "page.tsx").write_text('<form onSubmit={handleSubmit}><input /></form>')

    # Backend
    backend = tmp_path / "backend"
    backend.mkdir()
    (backend / "requirements.txt").write_text("fastapi>=0.110.0\n")
    (backend / "main.py").write_text('''
from fastapi import FastAPI
app = FastAPI()

@app.get("/api/v1/health")
def health():
    return {"status": "ok"}

@app.post("/api/v1/auth/login")
def login(body: dict):
    return {"token": "fake"}
''')

    return tmp_path


class TestDetectFrameworks:
    """Tests for detect_frameworks."""

    def test_detect_fullstack_project(self, fullstack_project: Path) -> None:
        """Should detect both Next.js and FastAPI in a fullstack project."""
        frameworks = detect_frameworks(fullstack_project)

        names = {f.name for f in frameworks}
        assert "nextjs" in names
        assert "fastapi" in names

    def test_detect_nextjs_only(self, tmp_path: Path) -> None:
        """Should detect only Next.js when there's no backend."""
        (tmp_path / "package.json").write_text('{"dependencies": {"next": "^14.0.0"}}')
        app_dir = tmp_path / "src" / "app"
        app_dir.mkdir(parents=True)
        (app_dir / "page.tsx").write_text("<h1>Hello</h1>")

        frameworks = detect_frameworks(tmp_path)
        assert len(frameworks) == 1
        assert frameworks[0].name == "nextjs"

    def test_detect_fastapi_only(self, tmp_path: Path) -> None:
        """Should detect only FastAPI when there's no frontend."""
        (tmp_path / "requirements.txt").write_text("fastapi>=0.110.0\n")
        (tmp_path / "main.py").write_text('''
from fastapi import FastAPI
app = FastAPI()

@app.get("/health")
def health():
    return {"ok": True}
''')

        frameworks = detect_frameworks(tmp_path)
        assert len(frameworks) == 1
        assert frameworks[0].name == "fastapi"

    def test_detect_empty_project(self, tmp_path: Path) -> None:
        """Should return empty list for projects with no recognized framework."""
        frameworks = detect_frameworks(tmp_path)
        assert frameworks == []

    def test_detect_express_project(self, tmp_path: Path) -> None:
        """Should detect Express.js projects."""
        (tmp_path / "package.json").write_text('{"dependencies": {"express": "^4.18.0"}}')
        (tmp_path / "index.js").write_text('''
const express = require("express");
const app = express();
app.get("/api/health", (req, res) => res.json({ ok: true }));
''')

        frameworks = detect_frameworks(tmp_path)
        assert len(frameworks) == 1
        assert frameworks[0].name == "express"

    def test_routes_aggregated(self, fullstack_project: Path) -> None:
        """Should discover routes for each detected framework."""
        frameworks = detect_frameworks(fullstack_project)

        for fw in frameworks:
            assert len(fw.routes) > 0, f"{fw.name} should have routes"

    def test_sample_app_detection(self) -> None:
        """Should detect frameworks in the sample app (if it exists)."""
        sample_app = Path(__file__).parent.parent / "examples" / "sample-app"
        if not sample_app.exists():
            pytest.skip("Sample app not found")

        frameworks = detect_frameworks(sample_app)
        names = {f.name for f in frameworks}
        assert "nextjs" in names
        assert "fastapi" in names
