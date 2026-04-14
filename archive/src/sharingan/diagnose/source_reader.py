"""Read relevant source code for failing components."""

from __future__ import annotations

from pathlib import Path


def read_source_context(file_path: str, project_dir: Path, context_lines: int = 50) -> str:
    """Read source code for a file, returning its content.

    Args:
        file_path: Relative path to the source file.
        project_dir: Root directory of the project.
        context_lines: Maximum number of lines to return.

    Returns:
        Source code content, truncated if necessary.
    """
    full_path = project_dir / file_path
    if not full_path.exists():
        return ""

    try:
        content = full_path.read_text(errors="replace")
    except OSError:
        return ""

    lines = content.splitlines()
    if len(lines) > context_lines:
        return "\n".join(lines[:context_lines]) + f"\n... ({len(lines) - context_lines} more lines)"

    return content


def find_related_files(source_file: str, project_dir: Path) -> list[str]:
    """Find files related to a source file (imports, components, etc.).

    Args:
        source_file: The primary source file path.
        project_dir: Root directory of the project.

    Returns:
        List of related file paths.
    """
    full_path = project_dir / source_file
    if not full_path.exists():
        return []

    related: list[str] = []

    # Check for sibling files (layout, loading, error, etc.)
    parent = full_path.parent
    for sibling in parent.iterdir():
        if sibling.is_file() and sibling != full_path:
            if sibling.suffix in (".tsx", ".ts", ".jsx", ".js", ".py"):
                related.append(str(sibling.relative_to(project_dir)))

    return related[:10]  # Limit to 10 related files
