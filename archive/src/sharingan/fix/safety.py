"""Safety checks before applying fixes."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from sharingan.config import SharinganConfig

# Files that should never be modified by automated fixes
PROTECTED_PATTERNS = [
    ".env",
    ".env.local",
    ".env.production",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
    ".git/",
    "node_modules/",
    ".next/",
    "__pycache__/",
    "*.sqlite",
    "*.db",
    "migrations/",
]


class SafetyCheck(BaseModel):
    """Result of a safety check."""

    is_safe: bool = Field(description="Whether it's safe to apply the fix")
    reason: str = Field(default="", description="Reason if not safe")
    file_path: str = Field(default="", description="File being checked")


def check_fix_safety(file_path: Path, config: SharinganConfig) -> SafetyCheck:
    """Check if it's safe to modify a file.

    Prevents modification of lock files, environment files,
    database files, and other protected resources.

    Args:
        file_path: Path to the file to check.
        config: Sharingan configuration.

    Returns:
        SafetyCheck indicating whether the modification is safe.
    """
    file_str = str(file_path)

    # Check protected patterns
    for pattern in PROTECTED_PATTERNS:
        if pattern.startswith("*."):
            if file_path.suffix == pattern[1:]:
                return SafetyCheck(
                    is_safe=False,
                    reason=f"File matches protected pattern: {pattern}",
                    file_path=file_str,
                )
        elif pattern.endswith("/"):
            if pattern.rstrip("/") in file_path.parts:
                return SafetyCheck(
                    is_safe=False,
                    reason=f"File is in protected directory: {pattern}",
                    file_path=file_str,
                )
        elif file_path.name == pattern:
            return SafetyCheck(
                is_safe=False,
                reason=f"File is protected: {pattern}",
                file_path=file_str,
            )

    # Check file is within project directory
    try:
        file_path.resolve().relative_to(config.project_dir.resolve())
    except ValueError:
        return SafetyCheck(
            is_safe=False,
            reason="File is outside the project directory",
            file_path=file_str,
        )

    # Check file is not too large (>1MB suggests generated/binary)
    if file_path.exists() and file_path.stat().st_size > 1_000_000:
        return SafetyCheck(
            is_safe=False,
            reason="File is too large (>1MB) — likely generated or binary",
            file_path=file_str,
        )

    return SafetyCheck(
        is_safe=True,
        file_path=file_str,
    )
