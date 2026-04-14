"""Fix application and test code based on diagnosis."""

from sharingan.fix.fixer import FixResult, apply_fix
from sharingan.fix.safety import SafetyCheck, check_fix_safety
from sharingan.fix.validator import validate_fix

__all__ = ["FixResult", "SafetyCheck", "apply_fix", "check_fix_safety", "validate_fix"]
