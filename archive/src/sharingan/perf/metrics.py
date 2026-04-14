"""Performance metrics data structures."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PerfMetrics(BaseModel):
    """Performance metrics captured for a page."""

    url: str = Field(description="URL that was measured")
    lcp_ms: float = Field(default=0, description="Largest Contentful Paint in ms")
    fcp_ms: float = Field(default=0, description="First Contentful Paint in ms")
    tti_ms: float = Field(default=0, description="Time to Interactive in ms")
    dom_content_loaded_ms: float = Field(default=0, description="DOMContentLoaded event in ms")
    load_ms: float = Field(default=0, description="Window load event in ms")
    total_size_kb: float = Field(default=0, description="Total transferred bytes in KB")
    request_count: int = Field(default=0, description="Number of network requests")


def format_metrics(metrics: PerfMetrics) -> str:
    """Format metrics as a human-readable string.

    Args:
        metrics: The performance metrics.

    Returns:
        Formatted multi-line string.
    """
    lines = [
        f"URL: {metrics.url}",
        f"  LCP: {metrics.lcp_ms:.0f} ms",
        f"  FCP: {metrics.fcp_ms:.0f} ms",
        f"  TTI: {metrics.tti_ms:.0f} ms",
        f"  DOMContentLoaded: {metrics.dom_content_loaded_ms:.0f} ms",
        f"  Load: {metrics.load_ms:.0f} ms",
        f"  Total size: {metrics.total_size_kb:.1f} KB",
        f"  Requests: {metrics.request_count}",
    ]
    return "\n".join(lines)
