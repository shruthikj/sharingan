"""Tests for the auth module."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from sharingan.auth.prod_guard import (
    ProdGuardError,
    check_prod_guard,
    is_safe_url,
)
from sharingan.auth.test_users import (
    TestUserCredentials,
    redact_credentials,
    resolve_test_user,
)
from sharingan.config import SharinganConfig


class TestIsSafeUrl:
    """Tests for is_safe_url."""

    @pytest.mark.parametrize("url", [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://0.0.0.0:8000",
        "http://192.168.1.5:3000",
        "http://10.0.0.3:3000",
        "https://dev.myapp.com",
        "https://staging.myapp.com",
        "https://stage.myapp.com",
        "https://qa.myapp.com",
        "http://myapp.local",
        "http://api.test",
    ])
    def test_safe_urls(self, url: str) -> None:
        """These URLs should be considered safe."""
        assert is_safe_url(url) is True

    @pytest.mark.parametrize("url", [
        "https://myapp.com",
        "https://www.myapp.com",
        "https://prod.myapp.com",
        "https://production.myapp.com",
        "https://live.myapp.com",
        "https://api.myapp.com",
    ])
    def test_unsafe_urls(self, url: str) -> None:
        """These URLs should be considered unsafe (look like prod)."""
        assert is_safe_url(url) is False


class TestCheckProdGuard:
    """Tests for check_prod_guard."""

    def test_allows_localhost(self, tmp_path: Path) -> None:
        """Should allow localhost URLs."""
        config = SharinganConfig(
            project_dir=tmp_path,
            base_url="http://localhost:3000",
            api_base_url="http://localhost:8000",
        )
        check_prod_guard(config)  # Should not raise

    def test_blocks_production(self, tmp_path: Path) -> None:
        """Should raise for production URLs."""
        config = SharinganConfig(
            project_dir=tmp_path,
            base_url="https://myapp.com",
        )
        with pytest.raises(ProdGuardError):
            check_prod_guard(config)

    def test_allows_prod_with_flag(self, tmp_path: Path) -> None:
        """Should allow production when allow_prod is True."""
        config = SharinganConfig(
            project_dir=tmp_path,
            base_url="https://myapp.com",
            allow_prod=True,
        )
        check_prod_guard(config)  # Should not raise

    def test_error_lists_unsafe_urls(self, tmp_path: Path) -> None:
        """Error should include the unsafe URLs."""
        config = SharinganConfig(
            project_dir=tmp_path,
            base_url="https://myapp.com",
            api_base_url="http://localhost:8000",
        )
        with pytest.raises(ProdGuardError, match="myapp.com"):
            check_prod_guard(config)


class TestResolveTestUser:
    """Tests for resolve_test_user."""

    def test_uses_config_password(self, tmp_path: Path) -> None:
        """Should use explicit password from config."""
        config = SharinganConfig(project_dir=tmp_path)
        config.test_user.password = "ConfigPass123!"

        creds = resolve_test_user(config)
        assert creds.password == "ConfigPass123!"
        assert creds.source == "config"

    def test_uses_env_vars(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should use env vars when config password is empty."""
        config = SharinganConfig(project_dir=tmp_path)
        monkeypatch.setenv("SHARINGAN_TEST_EMAIL", "env@example.local")
        monkeypatch.setenv("SHARINGAN_TEST_PASSWORD", "EnvPass123!")

        creds = resolve_test_user(config)
        assert creds.email == "env@example.local"
        assert creds.password == "EnvPass123!"
        assert creds.source == "env"

    def test_generates_new_credentials(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should generate new credentials when none are available."""
        config = SharinganConfig(project_dir=tmp_path)
        monkeypatch.delenv("SHARINGAN_TEST_EMAIL", raising=False)
        monkeypatch.delenv("SHARINGAN_TEST_PASSWORD", raising=False)

        creds = resolve_test_user(config)
        assert creds.source == "generated"
        assert len(creds.password) >= 16
        assert config.get_credentials_path().exists()

    def test_generated_password_is_complex(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Generated password should meet complexity requirements."""
        config = SharinganConfig(project_dir=tmp_path)
        monkeypatch.delenv("SHARINGAN_TEST_EMAIL", raising=False)
        monkeypatch.delenv("SHARINGAN_TEST_PASSWORD", raising=False)

        creds = resolve_test_user(config)
        pwd = creds.password
        assert any(c.islower() for c in pwd)
        assert any(c.isupper() for c in pwd)
        assert any(c.isdigit() for c in pwd)
        assert any(c in "!@#$%^&*" for c in pwd)

    def test_reuses_stored_credentials(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should reuse credentials from a previous run."""
        config = SharinganConfig(project_dir=tmp_path)
        monkeypatch.delenv("SHARINGAN_TEST_EMAIL", raising=False)
        monkeypatch.delenv("SHARINGAN_TEST_PASSWORD", raising=False)

        # First call generates
        creds1 = resolve_test_user(config)
        # Second call should reuse
        creds2 = resolve_test_user(config)

        assert creds1.password == creds2.password
        assert creds2.source == "stored"

    def test_gitignore_created(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should create .gitignore in .sharingan/ directory."""
        config = SharinganConfig(project_dir=tmp_path)
        monkeypatch.delenv("SHARINGAN_TEST_EMAIL", raising=False)
        monkeypatch.delenv("SHARINGAN_TEST_PASSWORD", raising=False)

        resolve_test_user(config)
        gitignore = tmp_path / ".sharingan" / ".gitignore"
        assert gitignore.exists()
        assert gitignore.read_text().strip() == "*"


class TestRedactCredentials:
    """Tests for redact_credentials."""

    def test_redacts_password(self) -> None:
        """Should replace password with [REDACTED]."""
        creds = TestUserCredentials(email="user@test.com", password="Secret123!", source="config")
        text = "Login with password Secret123! failed"
        result = redact_credentials(text, creds)
        assert "Secret123!" not in result
        assert "[REDACTED]" in result

    def test_handles_empty_password(self) -> None:
        """Should handle empty password gracefully."""
        creds = TestUserCredentials(email="user@test.com", password="", source="config")
        text = "Some log text"
        assert redact_credentials(text, creds) == text
