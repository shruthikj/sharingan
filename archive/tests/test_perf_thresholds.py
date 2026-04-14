"""Tests for the performance thresholds module."""

from __future__ import annotations

from sharingan.config import PerfConfig
from sharingan.perf.metrics import PerfMetrics, format_metrics
from sharingan.perf.thresholds import check_thresholds


class TestCheckThresholds:
    """Tests for check_thresholds."""

    def test_all_metrics_under_threshold(self) -> None:
        """Should pass when all metrics are under thresholds."""
        metrics = PerfMetrics(
            url="http://localhost/",
            lcp_ms=1500,
            fcp_ms=1000,
            tti_ms=2000,
            total_size_kb=500,
        )
        config = PerfConfig()
        result = check_thresholds(metrics, config)
        assert result.passed is True
        assert len(result.violations) == 0

    def test_lcp_violation(self) -> None:
        """Should fail when LCP is over threshold."""
        metrics = PerfMetrics(url="/", lcp_ms=5000, fcp_ms=1000, tti_ms=2000)
        result = check_thresholds(metrics, PerfConfig(max_lcp_ms=2500))
        assert result.passed is False
        assert any("LCP" in v for v in result.violations)

    def test_fcp_violation(self) -> None:
        """Should fail when FCP is over threshold."""
        metrics = PerfMetrics(url="/", fcp_ms=3000)
        result = check_thresholds(metrics, PerfConfig(max_fcp_ms=1800))
        assert result.passed is False
        assert any("FCP" in v for v in result.violations)

    def test_multiple_violations(self) -> None:
        """Should report all violations."""
        metrics = PerfMetrics(
            url="/",
            lcp_ms=5000,
            fcp_ms=3000,
            tti_ms=6000,
            total_size_kb=5000,
        )
        result = check_thresholds(metrics, PerfConfig())
        assert result.passed is False
        assert len(result.violations) >= 3

    def test_size_threshold(self) -> None:
        """Should check total page size."""
        metrics = PerfMetrics(url="/", total_size_kb=3000)
        result = check_thresholds(metrics, PerfConfig(max_total_size_kb=2000))
        assert result.passed is False
        assert any("size" in v.lower() for v in result.violations)


class TestFormatMetrics:
    """Tests for format_metrics."""

    def test_format_includes_url(self) -> None:
        """Formatted output should include the URL."""
        metrics = PerfMetrics(url="http://test/", lcp_ms=1000)
        output = format_metrics(metrics)
        assert "http://test/" in output

    def test_format_includes_all_metrics(self) -> None:
        """Formatted output should include all metric names."""
        metrics = PerfMetrics(
            url="/",
            lcp_ms=1000,
            fcp_ms=500,
            tti_ms=2000,
            total_size_kb=100,
        )
        output = format_metrics(metrics)
        assert "LCP" in output
        assert "FCP" in output
        assert "TTI" in output
