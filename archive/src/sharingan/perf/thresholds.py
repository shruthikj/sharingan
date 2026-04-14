"""Check performance metrics against configured thresholds."""

from __future__ import annotations

from pydantic import BaseModel, Field

from sharingan.config import PerfConfig
from sharingan.perf.metrics import PerfMetrics


class PerfThresholdResult(BaseModel):
    """Result of checking performance against thresholds."""

    passed: bool = Field(description="Whether all thresholds passed")
    violations: list[str] = Field(default_factory=list, description="Threshold violations")
    metrics: PerfMetrics = Field(description="The measured metrics")


def check_thresholds(metrics: PerfMetrics, perf_config: PerfConfig) -> PerfThresholdResult:
    """Check performance metrics against configured thresholds.

    Args:
        metrics: The measured performance metrics.
        perf_config: The threshold configuration.

    Returns:
        Result indicating whether thresholds passed, with violations listed.
    """
    violations: list[str] = []

    if metrics.lcp_ms > perf_config.max_lcp_ms:
        violations.append(
            f"LCP {metrics.lcp_ms:.0f}ms exceeds threshold {perf_config.max_lcp_ms}ms"
        )

    if metrics.fcp_ms > perf_config.max_fcp_ms:
        violations.append(
            f"FCP {metrics.fcp_ms:.0f}ms exceeds threshold {perf_config.max_fcp_ms}ms"
        )

    if metrics.tti_ms > perf_config.max_tti_ms:
        violations.append(
            f"TTI {metrics.tti_ms:.0f}ms exceeds threshold {perf_config.max_tti_ms}ms"
        )

    if metrics.total_size_kb > perf_config.max_total_size_kb:
        violations.append(
            f"Total size {metrics.total_size_kb:.0f}KB exceeds threshold {perf_config.max_total_size_kb}KB"
        )

    return PerfThresholdResult(
        passed=not violations,
        violations=violations,
        metrics=metrics,
    )
