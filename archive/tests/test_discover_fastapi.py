"""Tests for FastAPI endpoint discovery."""

from __future__ import annotations

from pathlib import Path

import pytest

from sharingan.discover.fastapi import FastAPIDiscoverer


@pytest.fixture
def sample_fastapi_project(tmp_path: Path) -> Path:
    """Create a minimal FastAPI project structure."""
    (tmp_path / "requirements.txt").write_text("fastapi>=0.110.0\nuvicorn>=0.29.0\n")

    (tmp_path / "main.py").write_text('''
from fastapi import FastAPI, Depends
from pydantic import BaseModel

app = FastAPI()

class ItemCreate(BaseModel):
    name: str

def get_current_user():
    pass

@app.get("/api/v1/health")
def health():
    return {"status": "ok"}

@app.post("/api/v1/auth/login")
def login(body: dict):
    return {"token": "fake"}

@app.get("/api/v1/items")
def list_items():
    return {"items": []}

@app.post("/api/v1/items")
def create_item(item: ItemCreate):
    return {"id": 1, "name": item.name}

@app.get("/api/v1/items/{item_id}")
def get_item(item_id: int):
    return {"id": item_id}

@app.get("/api/v1/protected")
def protected(user=Depends(get_current_user)):
    return {"user": "ok"}
''')

    return tmp_path


class TestFastAPIDiscoverer:
    """Tests for FastAPIDiscoverer."""

    def test_detect_fastapi_project(self, sample_fastapi_project: Path) -> None:
        """Should detect FastAPI from requirements.txt."""
        discoverer = FastAPIDiscoverer()
        result = discoverer.detect(sample_fastapi_project)

        assert result is not None
        assert result.name == "fastapi"
        assert result.category == "backend"

    def test_detect_non_fastapi_project(self, tmp_path: Path) -> None:
        """Should return None for non-FastAPI projects."""
        (tmp_path / "requirements.txt").write_text("django>=4.0\n")
        discoverer = FastAPIDiscoverer()
        result = discoverer.detect(tmp_path)
        assert result is None

    def test_detect_no_requirements(self, tmp_path: Path) -> None:
        """Should return None when no requirements file exists."""
        discoverer = FastAPIDiscoverer()
        result = discoverer.detect(tmp_path)
        assert result is None

    def test_discover_endpoints(self, sample_fastapi_project: Path) -> None:
        """Should discover all API endpoints."""
        discoverer = FastAPIDiscoverer()
        result = discoverer.detect(sample_fastapi_project)
        assert result is not None

        paths = {(r.path, r.method) for r in result.routes}
        assert ("/api/v1/health", "GET") in paths
        assert ("/api/v1/auth/login", "POST") in paths
        assert ("/api/v1/items", "GET") in paths
        assert ("/api/v1/items", "POST") in paths

    def test_discover_auth_endpoints(self, sample_fastapi_project: Path) -> None:
        """Should detect endpoints with auth dependencies."""
        discoverer = FastAPIDiscoverer()
        result = discoverer.detect(sample_fastapi_project)
        assert result is not None

        protected = [r for r in result.routes if r.path == "/api/v1/protected"]
        assert len(protected) == 1
        assert protected[0].has_auth is True

    def test_discover_dynamic_params(self, sample_fastapi_project: Path) -> None:
        """Should detect dynamic path parameters."""
        discoverer = FastAPIDiscoverer()
        result = discoverer.detect(sample_fastapi_project)
        assert result is not None

        item_detail = [r for r in result.routes if "{item_id}" in r.path]
        assert len(item_detail) >= 1
        assert "item_id" in item_detail[0].dynamic_params

    def test_all_routes_are_api_type(self, sample_fastapi_project: Path) -> None:
        """All FastAPI routes should be classified as API type."""
        discoverer = FastAPIDiscoverer()
        result = discoverer.detect(sample_fastapi_project)
        assert result is not None

        for route in result.routes:
            assert route.route_type == "api"

    def test_nested_in_backend_dir(self, tmp_path: Path) -> None:
        """Should detect FastAPI in a backend/ subdirectory."""
        backend = tmp_path / "backend"
        backend.mkdir()
        (backend / "requirements.txt").write_text("fastapi>=0.110.0\n")
        (backend / "main.py").write_text('''
from fastapi import FastAPI
app = FastAPI()

@app.get("/health")
def health():
    return {"ok": True}
''')

        discoverer = FastAPIDiscoverer()
        result = discoverer.detect(tmp_path)
        assert result is not None
        assert len(result.routes) >= 1
