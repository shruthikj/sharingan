"""Test user credential management with fallback chain."""

from __future__ import annotations

import json
import os
import secrets
import string
from pathlib import Path

from pydantic import BaseModel, Field

from sharingan.config import SharinganConfig


class TestUserCredentials(BaseModel):
    """Resolved test user credentials."""

    email: str = Field(description="Test user email")
    password: str = Field(description="Test user password")
    source: str = Field(description="Where credentials came from: config, env, stored, generated")


def resolve_test_user(config: SharinganConfig) -> TestUserCredentials:
    """Resolve test user credentials using a fallback chain.

    Order of precedence:
    1. Explicit password in config
    2. Env vars SHARINGAN_TEST_EMAIL / SHARINGAN_TEST_PASSWORD
    3. Previously stored credentials in .sharingan/credentials.json
    4. Generate new credentials and store them

    Args:
        config: Sharingan configuration.

    Returns:
        Resolved test user credentials.
    """
    # 1. Explicit config
    if config.test_user.password:
        return TestUserCredentials(
            email=config.test_user.email,
            password=config.test_user.password,
            source="config",
        )

    # 2. Env vars
    env_email = os.environ.get("SHARINGAN_TEST_EMAIL")
    env_password = os.environ.get("SHARINGAN_TEST_PASSWORD")
    if env_email and env_password:
        return TestUserCredentials(
            email=env_email,
            password=env_password,
            source="env",
        )

    # 3. Stored credentials
    creds_path = config.get_credentials_path()
    if creds_path.exists():
        try:
            data = json.loads(creds_path.read_text())
            if "email" in data and "password" in data:
                return TestUserCredentials(
                    email=data["email"],
                    password=data["password"],
                    source="stored",
                )
        except (json.JSONDecodeError, OSError):
            pass

    # 4. Generate new
    password = _generate_password()
    creds = TestUserCredentials(
        email=config.test_user.email,
        password=password,
        source="generated",
    )
    _store_credentials(creds, creds_path)
    return creds


def _generate_password(length: int = 20) -> str:
    """Generate a strong random password meeting typical complexity requirements."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    # Ensure at least one of each category
    while True:
        password = "".join(secrets.choice(alphabet) for _ in range(length))
        if (
            any(c.islower() for c in password)
            and any(c.isupper() for c in password)
            and any(c.isdigit() for c in password)
            and any(c in "!@#$%^&*" for c in password)
        ):
            return password


def _store_credentials(creds: TestUserCredentials, path: Path) -> None:
    """Store credentials to a gitignored file with restricted permissions."""
    path.parent.mkdir(parents=True, exist_ok=True)

    # Ensure .sharingan/ is gitignored
    gitignore = path.parent / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text("*\n")

    path.write_text(json.dumps({"email": creds.email, "password": creds.password}, indent=2))

    # Restrict permissions to owner only
    try:
        path.chmod(0o600)
    except OSError:
        pass


def redact_credentials(text: str, creds: TestUserCredentials) -> str:
    """Redact credentials from a string (for logs/reports).

    Args:
        text: Input text that may contain credentials.
        creds: Credentials to redact.

    Returns:
        Text with password replaced by [REDACTED].
    """
    if not creds.password:
        return text
    return text.replace(creds.password, "[REDACTED]")
