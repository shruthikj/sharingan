"""Test failure diagnosis — determine if failures are test bugs or application bugs."""

from sharingan.diagnose.analyzer import Diagnosis, DiagnosisType, analyze_failure
from sharingan.diagnose.fix_classifier import FixClassification, FixType, classify_fix

__all__ = ["Diagnosis", "DiagnosisType", "FixClassification", "FixType", "analyze_failure", "classify_fix"]
