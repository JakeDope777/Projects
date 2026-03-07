"""
Competitive Benchmarking Engine — Industry & Competitor Comparison

Provides benchmark data for comparing your metrics against:
  1. Industry averages (by vertical)
  2. Competitor estimates (when available)
  3. Best-in-class targets

Includes built-in benchmark databases for common marketing verticals
and supports custom benchmark imports.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------

@dataclass
class BenchmarkComparison:
    """Comparison of a single metric against benchmarks."""
    metric: str
    your_value: float
    industry_avg: float
    industry_p25: float  # 25th percentile
    industry_p75: float  # 75th percentile
    best_in_class: float
    percentile_rank: float  # Where you fall (0-100)
    gap_to_avg: float  # Difference from industry average
    gap_to_best: float  # Difference from best-in-class
    assessment: str  # "below_average", "average", "above_average", "best_in_class"


@dataclass
class BenchmarkReport:
    """Full benchmarking report."""
    industry: str
    comparisons: list[BenchmarkComparison]
    overall_score: float  # 0-100 composite score
    strengths: list[str]
    weaknesses: list[str]
    generated_at: str = ""


# ---------------------------------------------------------------------------
# Industry Benchmark Database
# ---------------------------------------------------------------------------

# Benchmark data by industry vertical
# Format: {metric: (avg, p25, p75, best_in_class)}
# Sources: Compiled from public marketing benchmark reports

INDUSTRY_BENCHMARKS: dict[str, dict[str, tuple[float, float, float, float]]] = {
    "saas": {
        "ctr": (2.5, 1.5, 3.5, 6.0),
        "conversion_rate": (3.0, 1.5, 5.0, 10.0),
        "cac": (200.0, 300.0, 120.0, 50.0),  # Lower is better
        "ltv": (2000.0, 800.0, 4000.0, 10000.0),
        "ltv_cac_ratio": (3.5, 2.0, 5.0, 10.0),
        "churn_rate": (5.0, 8.0, 3.0, 1.0),  # Lower is better
        "retention_rate": (95.0, 92.0, 97.0, 99.0),
        "roas": (4.0, 2.0, 6.0, 12.0),
        "email_open_rate": (22.0, 15.0, 28.0, 40.0),
        "email_click_rate": (3.5, 2.0, 5.0, 8.0),
        "bounce_rate": (45.0, 55.0, 35.0, 20.0),  # Lower is better
        "activation_rate": (40.0, 25.0, 55.0, 80.0),
        "net_promoter_score": (30.0, 10.0, 50.0, 70.0),
        "viral_coefficient": (0.5, 0.2, 0.8, 1.5),
        "signup_rate": (3.0, 1.5, 5.0, 10.0),
        "arpu": (100.0, 40.0, 200.0, 500.0),
        "cpc": (2.50, 4.00, 1.50, 0.50),  # Lower is better
        "cpm": (15.0, 25.0, 10.0, 5.0),  # Lower is better
    },
    "ecommerce": {
        "ctr": (1.8, 1.0, 2.5, 5.0),
        "conversion_rate": (2.5, 1.0, 4.0, 8.0),
        "cac": (45.0, 80.0, 25.0, 10.0),
        "ltv": (300.0, 100.0, 600.0, 2000.0),
        "ltv_cac_ratio": (5.0, 2.5, 8.0, 15.0),
        "churn_rate": (25.0, 35.0, 15.0, 5.0),
        "retention_rate": (75.0, 65.0, 85.0, 95.0),
        "roas": (5.0, 2.5, 8.0, 15.0),
        "email_open_rate": (18.0, 12.0, 24.0, 35.0),
        "email_click_rate": (2.5, 1.5, 4.0, 7.0),
        "bounce_rate": (40.0, 50.0, 30.0, 15.0),
        "net_promoter_score": (35.0, 15.0, 50.0, 75.0),
        "arpu": (75.0, 30.0, 150.0, 400.0),
        "cpc": (1.20, 2.00, 0.80, 0.30),
        "cpm": (10.0, 18.0, 6.0, 3.0),
    },
    "b2b": {
        "ctr": (2.0, 1.2, 3.0, 5.5),
        "conversion_rate": (2.0, 1.0, 3.5, 7.0),
        "cac": (500.0, 800.0, 300.0, 100.0),
        "ltv": (5000.0, 2000.0, 10000.0, 50000.0),
        "ltv_cac_ratio": (4.0, 2.0, 6.0, 12.0),
        "churn_rate": (8.0, 12.0, 5.0, 2.0),
        "retention_rate": (92.0, 88.0, 95.0, 98.0),
        "roas": (3.5, 1.5, 5.5, 10.0),
        "email_open_rate": (20.0, 14.0, 26.0, 38.0),
        "email_click_rate": (3.0, 1.8, 4.5, 7.5),
        "bounce_rate": (50.0, 60.0, 40.0, 25.0),
        "lead_to_mql_rate": (15.0, 8.0, 25.0, 40.0),
        "mql_to_sql_rate": (20.0, 10.0, 30.0, 50.0),
        "demo_request_rate": (1.5, 0.5, 3.0, 6.0),
        "net_promoter_score": (25.0, 5.0, 45.0, 65.0),
        "arpu": (500.0, 200.0, 1000.0, 5000.0),
        "cpc": (3.50, 6.00, 2.00, 0.80),
        "cpm": (20.0, 35.0, 12.0, 6.0),
    },
    "fintech": {
        "ctr": (1.5, 0.8, 2.2, 4.0),
        "conversion_rate": (2.0, 0.8, 3.5, 7.0),
        "cac": (300.0, 500.0, 180.0, 60.0),
        "ltv": (3000.0, 1000.0, 6000.0, 15000.0),
        "ltv_cac_ratio": (4.0, 2.0, 6.0, 12.0),
        "churn_rate": (6.0, 10.0, 3.0, 1.5),
        "retention_rate": (94.0, 90.0, 97.0, 99.0),
        "roas": (3.5, 1.5, 5.5, 10.0),
        "email_open_rate": (20.0, 13.0, 26.0, 36.0),
        "email_click_rate": (2.8, 1.5, 4.0, 7.0),
        "bounce_rate": (48.0, 58.0, 38.0, 22.0),
        "net_promoter_score": (28.0, 8.0, 48.0, 68.0),
        "arpu": (150.0, 60.0, 300.0, 800.0),
        "cpc": (3.00, 5.00, 1.80, 0.60),
        "cpm": (18.0, 30.0, 10.0, 5.0),
    },
    "healthcare": {
        "ctr": (1.8, 1.0, 2.5, 4.5),
        "conversion_rate": (2.5, 1.2, 4.0, 7.5),
        "cac": (250.0, 400.0, 150.0, 50.0),
        "ltv": (4000.0, 1500.0, 8000.0, 20000.0),
        "roas": (3.0, 1.5, 5.0, 9.0),
        "email_open_rate": (24.0, 16.0, 30.0, 42.0),
        "email_click_rate": (3.2, 2.0, 4.5, 7.5),
        "bounce_rate": (42.0, 52.0, 32.0, 18.0),
        "net_promoter_score": (32.0, 12.0, 52.0, 72.0),
        "cpc": (2.80, 4.50, 1.60, 0.50),
        "cpm": (16.0, 28.0, 9.0, 4.0),
    },
}

# Metrics where lower is better
_LOWER_IS_BETTER = {"cac", "churn_rate", "bounce_rate", "cpc", "cpm", "email_bounce_rate", "email_unsubscribe_rate"}


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class BenchmarkingEngine:
    """Compare your metrics against industry benchmarks."""

    def __init__(self, custom_benchmarks: Optional[dict[str, dict]] = None):
        self.custom_benchmarks = custom_benchmarks or {}

    def get_supported_industries(self) -> list[str]:
        """Return list of industries with available benchmarks."""
        return sorted(set(list(INDUSTRY_BENCHMARKS.keys()) + list(self.custom_benchmarks.keys())))

    def compare(
        self,
        your_metrics: dict[str, float],
        industry: str = "saas",
    ) -> BenchmarkReport:
        """
        Compare your metrics against industry benchmarks.

        Args:
            your_metrics: Dict of metric name → your value.
            industry: Industry vertical for benchmark comparison.

        Returns:
            BenchmarkReport with comparisons and assessment.
        """
        benchmarks = self.custom_benchmarks.get(
            industry, INDUSTRY_BENCHMARKS.get(industry, INDUSTRY_BENCHMARKS["saas"])
        )

        comparisons: list[BenchmarkComparison] = []
        strengths: list[str] = []
        weaknesses: list[str] = []

        for metric, your_value in your_metrics.items():
            if not isinstance(your_value, (int, float)):
                continue
            if metric not in benchmarks:
                continue

            avg, p25, p75, best = benchmarks[metric]
            lower_better = metric in _LOWER_IS_BETTER

            # Calculate percentile rank
            pct_rank = self._percentile_rank(
                float(your_value), avg, p25, p75, best, lower_better
            )

            # Gap calculations
            gap_to_avg = round(float(your_value) - avg, 2)
            gap_to_best = round(float(your_value) - best, 2)

            # Assessment
            if lower_better:
                if your_value <= best:
                    assessment = "best_in_class"
                elif your_value <= avg:
                    assessment = "above_average"
                elif your_value <= p25:
                    assessment = "average"
                else:
                    assessment = "below_average"
            else:
                if your_value >= best:
                    assessment = "best_in_class"
                elif your_value >= avg:
                    assessment = "above_average"
                elif your_value >= p25:
                    assessment = "average"
                else:
                    assessment = "below_average"

            comp = BenchmarkComparison(
                metric=metric,
                your_value=round(float(your_value), 2),
                industry_avg=avg,
                industry_p25=p25,
                industry_p75=p75,
                best_in_class=best,
                percentile_rank=round(pct_rank, 1),
                gap_to_avg=gap_to_avg,
                gap_to_best=gap_to_best,
                assessment=assessment,
            )
            comparisons.append(comp)

            if assessment in ("above_average", "best_in_class"):
                strengths.append(f"{metric}: {your_value} (industry avg: {avg})")
            elif assessment == "below_average":
                weaknesses.append(f"{metric}: {your_value} (industry avg: {avg})")

        # Overall score (average percentile rank)
        overall_score = 0.0
        if comparisons:
            overall_score = round(
                sum(c.percentile_rank for c in comparisons) / len(comparisons), 1
            )

        return BenchmarkReport(
            industry=industry,
            comparisons=comparisons,
            overall_score=overall_score,
            strengths=strengths,
            weaknesses=weaknesses,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    def add_custom_benchmarks(
        self,
        industry: str,
        benchmarks: dict[str, tuple[float, float, float, float]],
    ) -> None:
        """Add or override benchmarks for a custom industry."""
        self.custom_benchmarks[industry] = benchmarks

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _percentile_rank(
        value: float,
        avg: float,
        p25: float,
        p75: float,
        best: float,
        lower_better: bool,
    ) -> float:
        """Estimate percentile rank based on known distribution points."""
        if lower_better:
            # Invert: lower value = higher percentile
            if value <= best:
                return 95.0
            elif value <= p75:
                # Between best and p75 → 75-95
                span = p75 - best if p75 != best else 1.0
                return 75.0 + (p75 - value) / span * 20.0
            elif value <= avg:
                # Between p75 and avg → 50-75
                span = avg - p75 if avg != p75 else 1.0
                return 50.0 + (avg - value) / span * 25.0
            elif value <= p25:
                # Between avg and p25 → 25-50
                span = p25 - avg if p25 != avg else 1.0
                return 25.0 + (p25 - value) / span * 25.0
            else:
                # Worse than p25
                return max(5.0, 25.0 - (value - p25) / max(p25, 1) * 25.0)
        else:
            # Higher is better
            if value >= best:
                return 95.0
            elif value >= p75:
                span = best - p75 if best != p75 else 1.0
                return 75.0 + (value - p75) / span * 20.0
            elif value >= avg:
                span = p75 - avg if p75 != avg else 1.0
                return 50.0 + (value - avg) / span * 25.0
            elif value >= p25:
                span = avg - p25 if avg != p25 else 1.0
                return 25.0 + (value - p25) / span * 25.0
            else:
                return max(5.0, 25.0 - (p25 - value) / max(p25, 1) * 25.0)
