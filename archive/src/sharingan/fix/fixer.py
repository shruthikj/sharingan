"""Apply fixes to application or test code."""

from __future__ import annotations

import shutil
from pathlib import Path

from pydantic import BaseModel, Field

from sharingan.config import SharinganConfig
from sharingan.diagnose.analyzer import Diagnosis
from sharingan.fix.safety import check_fix_safety


class FixResult(BaseModel):
    """Result of applying a fix."""

    success: bool = Field(description="Whether the fix was applied successfully")
    file_path: str = Field(description="File that was modified")
    backup_path: str = Field(default="", description="Path to backup of original file")
    description: str = Field(description="Description of the fix applied")
    diff_summary: str = Field(default="", description="Summary of changes made")


def apply_fix(
    diagnosis: Diagnosis,
    fix_content: str,
    config: SharinganConfig,
) -> FixResult:
    """Apply a fix to a file based on the diagnosis.

    This function is primarily used as a utility by the Claude Code slash command,
    which handles the actual code editing. This provides the safety checks and
    backup mechanism.

    Args:
        diagnosis: The failure diagnosis with suggested file.
        fix_content: The new content for the file.
        config: Sharingan configuration.

    Returns:
        FixResult indicating success or failure.
    """
    if not diagnosis.suggested_file:
        return FixResult(
            success=False,
            file_path="",
            description="No file to fix — diagnosis did not identify a target file",
        )

    target_path = config.project_dir / diagnosis.suggested_file

    # Safety check
    safety = check_fix_safety(target_path, config)
    if not safety.is_safe:
        return FixResult(
            success=False,
            file_path=diagnosis.suggested_file,
            description=f"Fix blocked by safety check: {safety.reason}",
        )

    # Create backup
    backup_path = _create_backup(target_path)

    try:
        target_path.write_text(fix_content)
        return FixResult(
            success=True,
            file_path=diagnosis.suggested_file,
            backup_path=str(backup_path) if backup_path else "",
            description=f"Applied fix to {diagnosis.suggested_file}",
        )
    except OSError as e:
        return FixResult(
            success=False,
            file_path=diagnosis.suggested_file,
            description=f"Failed to write fix: {e}",
        )


def rollback_fix(fix_result: FixResult, config: SharinganConfig) -> bool:
    """Roll back a fix by restoring the backup.

    Args:
        fix_result: The fix result containing backup path.
        config: Sharingan configuration.

    Returns:
        True if rollback succeeded.
    """
    if not fix_result.backup_path:
        return False

    backup = Path(fix_result.backup_path)
    target = config.project_dir / fix_result.file_path

    if not backup.exists():
        return False

    try:
        shutil.copy2(backup, target)
        backup.unlink()
        return True
    except OSError:
        return False


def _create_backup(file_path: Path) -> Path | None:
    """Create a backup of a file before modifying it."""
    if not file_path.exists():
        return None

    backup_dir = file_path.parent / ".sharingan-backups"
    backup_dir.mkdir(exist_ok=True)

    backup_path = backup_dir / f"{file_path.name}.bak"
    try:
        shutil.copy2(file_path, backup_path)
        return backup_path
    except OSError:
        return None
