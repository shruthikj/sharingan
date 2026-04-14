"""Classify what type of fix is needed for a diagnosis."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from sharingan.diagnose.analyzer import Diagnosis, DiagnosisType


class FixType(str, Enum):
    """Classification of fix type."""

    FRONTEND = "frontend"
    BACKEND = "backend"
    API = "api"
    CONFIG = "config"
    TEST = "test"
    MIDDLEWARE = "middleware"


class FixClassification(BaseModel):
    """Classification of a fix."""

    fix_type: FixType = Field(description="Type of fix needed")
    target_file: str = Field(description="File to modify")
    description: str = Field(description="Description of what to fix")
    complexity: str = Field(default="simple", description="Fix complexity: simple, moderate, complex")


def classify_fix(diagnosis: Diagnosis) -> FixClassification:
    """Classify what type of fix is needed based on the diagnosis.

    Args:
        diagnosis: The failure diagnosis.

    Returns:
        Classification of the fix needed.
    """
    if diagnosis.diagnosis_type == DiagnosisType.TEST_BUG:
        return FixClassification(
            fix_type=FixType.TEST,
            target_file=diagnosis.suggested_file,
            description=f"Fix test: {diagnosis.summary}",
            complexity="simple",
        )

    target = diagnosis.suggested_file.lower()

    if diagnosis.diagnosis_type == DiagnosisType.CONFIG_ISSUE:
        return FixClassification(
            fix_type=FixType.CONFIG,
            target_file=diagnosis.suggested_file,
            description=f"Fix config: {diagnosis.summary}",
            complexity="moderate",
        )

    # Classify app bugs by file path
    if any(kw in target for kw in ["middleware", "middleware.ts", "middleware.js"]):
        fix_type = FixType.MIDDLEWARE
    elif any(kw in target for kw in ["api/", "route.ts", "route.js", "main.py", "views.py"]):
        fix_type = FixType.API
    elif any(kw in target for kw in [".py", "backend/"]):
        fix_type = FixType.BACKEND
    else:
        fix_type = FixType.FRONTEND

    # Estimate complexity based on error pattern
    complexity = "simple"
    if "state management" in diagnosis.summary.lower():
        complexity = "complex"
    elif any(kw in diagnosis.summary.lower() for kw in ["auth", "permission", "cors"]):
        complexity = "moderate"

    return FixClassification(
        fix_type=fix_type,
        target_file=diagnosis.suggested_file,
        description=f"Fix {fix_type.value}: {diagnosis.summary}",
        complexity=complexity,
    )
