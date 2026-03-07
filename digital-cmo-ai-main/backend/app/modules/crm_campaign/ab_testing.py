"""
A/B Testing Engine for Campaigns

Provides a complete A/B (and multivariate) testing framework for marketing
campaigns with statistical significance tracking, sample size calculation,
and automated winner selection.

Features:
- Create A/B and A/B/n tests for campaigns
- Track variant performance in real time
- Statistical significance calculation (z-test for proportions)
- Minimum sample size estimation
- Automatic winner declaration at confidence threshold
- Sequential testing with early stopping
- Test history and reporting
"""

import math
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional
from enum import Enum
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class TestStatus(str, Enum):
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TestMetric(str, Enum):
    OPEN_RATE = "open_rate"
    CLICK_RATE = "click_rate"
    CONVERSION_RATE = "conversion_rate"
    REVENUE_PER_SEND = "revenue_per_send"
    UNSUBSCRIBE_RATE = "unsubscribe_rate"


# ---------------------------------------------------------------------------
# Statistical utilities
# ---------------------------------------------------------------------------

class StatisticalCalculator:
    """Statistical functions for A/B test analysis."""

    @staticmethod
    def z_score(p1: float, p2: float, n1: int, n2: int) -> float:
        """
        Calculate the z-score for a two-proportion z-test.

        Args:
            p1: Proportion for variant A (control).
            p2: Proportion for variant B (treatment).
            n1: Sample size for variant A.
            n2: Sample size for variant B.

        Returns:
            z-score value.
        """
        if n1 == 0 or n2 == 0:
            return 0.0

        p_pool = (p1 * n1 + p2 * n2) / (n1 + n2)
        if p_pool == 0 or p_pool == 1:
            return 0.0

        se = math.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
        if se == 0:
            return 0.0

        return (p2 - p1) / se

    @staticmethod
    def p_value_from_z(z: float) -> float:
        """
        Approximate two-tailed p-value from z-score using the
        Abramowitz and Stegun approximation of the normal CDF.
        """
        # Approximation of the standard normal CDF
        def norm_cdf(x: float) -> float:
            if x < -8:
                return 0.0
            if x > 8:
                return 1.0
            a1 = 0.254829592
            a2 = -0.284496736
            a3 = 1.421413741
            a4 = -1.453152027
            a5 = 1.061405429
            p = 0.3275911
            sign = 1 if x >= 0 else -1
            x_abs = abs(x) / math.sqrt(2)
            t = 1.0 / (1.0 + p * x_abs)
            y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * math.exp(-x_abs * x_abs)
            return 0.5 * (1.0 + sign * y)

        return 2 * (1 - norm_cdf(abs(z)))

    @staticmethod
    def confidence_level(p_value: float) -> float:
        """Convert p-value to confidence level (percentage)."""
        return max(0.0, min(100.0, (1 - p_value) * 100))

    @staticmethod
    def minimum_sample_size(
        baseline_rate: float,
        minimum_detectable_effect: float,
        alpha: float = 0.05,
        power: float = 0.80,
    ) -> int:
        """
        Calculate minimum sample size per variant for a two-proportion test.

        Args:
            baseline_rate: Expected baseline conversion rate.
            minimum_detectable_effect: Minimum relative effect to detect (e.g., 0.1 for 10%).
            alpha: Significance level (default 0.05).
            power: Statistical power (default 0.80).

        Returns:
            Minimum sample size per variant.
        """
        p1 = baseline_rate
        p2 = baseline_rate * (1 + minimum_detectable_effect)

        if p1 <= 0 or p1 >= 1 or p2 <= 0 or p2 >= 1:
            return 1000  # Fallback

        # Z-values for alpha and power
        z_alpha = 1.96 if alpha == 0.05 else 2.576 if alpha == 0.01 else 1.645
        z_power = 0.842 if power == 0.80 else 1.282 if power == 0.90 else 0.674

        numerator = (z_alpha * math.sqrt(2 * p1 * (1 - p1)) +
                     z_power * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2
        denominator = (p2 - p1) ** 2

        if denominator == 0:
            return 1000

        return int(math.ceil(numerator / denominator))

    @staticmethod
    def relative_lift(control_rate: float, treatment_rate: float) -> float:
        """Calculate relative lift of treatment over control."""
        if control_rate == 0:
            return 0.0
        return (treatment_rate - control_rate) / control_rate


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class TestVariant:
    """A single variant in an A/B test."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    content: dict = field(default_factory=dict)
    is_control: bool = False
    traffic_percentage: float = 50.0

    # Metrics
    sends: int = 0
    opens: int = 0
    clicks: int = 0
    conversions: int = 0
    revenue: float = 0.0
    unsubscribes: int = 0

    @property
    def open_rate(self) -> float:
        return self.opens / max(self.sends, 1)

    @property
    def click_rate(self) -> float:
        return self.clicks / max(self.sends, 1)

    @property
    def conversion_rate(self) -> float:
        return self.conversions / max(self.sends, 1)

    @property
    def revenue_per_send(self) -> float:
        return self.revenue / max(self.sends, 1)

    @property
    def unsubscribe_rate(self) -> float:
        return self.unsubscribes / max(self.sends, 1)

    def get_metric(self, metric: TestMetric) -> float:
        metric_map = {
            TestMetric.OPEN_RATE: self.open_rate,
            TestMetric.CLICK_RATE: self.click_rate,
            TestMetric.CONVERSION_RATE: self.conversion_rate,
            TestMetric.REVENUE_PER_SEND: self.revenue_per_send,
            TestMetric.UNSUBSCRIBE_RATE: self.unsubscribe_rate,
        }
        return metric_map.get(metric, 0.0)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "is_control": self.is_control,
            "traffic_percentage": self.traffic_percentage,
            "metrics": {
                "sends": self.sends,
                "opens": self.opens,
                "clicks": self.clicks,
                "conversions": self.conversions,
                "revenue": round(self.revenue, 2),
                "unsubscribes": self.unsubscribes,
            },
            "rates": {
                "open_rate": round(self.open_rate, 4),
                "click_rate": round(self.click_rate, 4),
                "conversion_rate": round(self.conversion_rate, 4),
                "revenue_per_send": round(self.revenue_per_send, 4),
                "unsubscribe_rate": round(self.unsubscribe_rate, 4),
            },
        }


@dataclass
class ABTest:
    """An A/B test definition with variants and results."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    campaign_id: str = ""
    name: str = ""
    description: str = ""
    primary_metric: TestMetric = TestMetric.CLICK_RATE
    status: TestStatus = TestStatus.DRAFT
    variants: list[TestVariant] = field(default_factory=list)
    confidence_threshold: float = 95.0  # Required confidence to declare winner
    min_sample_per_variant: int = 100
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    winner_variant_id: Optional[str] = None
    winner_confidence: float = 0.0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "campaign_id": self.campaign_id,
            "name": self.name,
            "description": self.description,
            "primary_metric": self.primary_metric.value,
            "status": self.status.value,
            "variants": [v.to_dict() for v in self.variants],
            "confidence_threshold": self.confidence_threshold,
            "min_sample_per_variant": self.min_sample_per_variant,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "winner_variant_id": self.winner_variant_id,
            "winner_confidence": round(self.winner_confidence, 2),
        }


# ---------------------------------------------------------------------------
# A/B Testing Engine
# ---------------------------------------------------------------------------

class ABTestingEngine:
    """
    Manages A/B tests for campaigns, tracks variant performance,
    and determines statistical significance.
    """

    def __init__(self):
        self._tests: dict[str, ABTest] = {}
        self._calculator = StatisticalCalculator()

    # ---- Test management ---------------------------------------------------

    def create_test(
        self,
        campaign_id: str,
        name: str,
        variants: list[dict],
        primary_metric: str = "click_rate",
        confidence_threshold: float = 95.0,
        description: str = "",
    ) -> dict:
        """
        Create a new A/B test.

        Args:
            campaign_id: Associated campaign ID.
            name: Test name.
            variants: List of variant dicts with name, content, is_control, traffic_percentage.
            primary_metric: The metric to optimise.
            confidence_threshold: Required confidence level to declare a winner.
            description: Test description.
        """
        test_variants = []
        has_control = False
        total_traffic = 0.0

        for v in variants:
            variant = TestVariant(
                name=v.get("name", f"Variant {len(test_variants) + 1}"),
                description=v.get("description", ""),
                content=v.get("content", {}),
                is_control=v.get("is_control", False),
                traffic_percentage=v.get("traffic_percentage", 100 / len(variants)),
            )
            if variant.is_control:
                has_control = True
            total_traffic += variant.traffic_percentage
            test_variants.append(variant)

        # Auto-assign control if none specified
        if not has_control and test_variants:
            test_variants[0].is_control = True

        # Calculate minimum sample size
        baseline = 0.025  # Default 2.5% baseline
        min_sample = self._calculator.minimum_sample_size(baseline, 0.1)

        test = ABTest(
            campaign_id=campaign_id,
            name=name,
            description=description,
            primary_metric=TestMetric(primary_metric),
            variants=test_variants,
            confidence_threshold=confidence_threshold,
            min_sample_per_variant=min_sample,
        )
        self._tests[test.id] = test

        return {
            "status": "success",
            "details": test.to_dict(),
            "logs": [f"A/B test '{name}' created with {len(test_variants)} variants"],
        }

    def start_test(self, test_id: str) -> dict:
        """Start an A/B test."""
        test = self._tests.get(test_id)
        if not test:
            return {"status": "error", "details": {"message": "Test not found"}}

        if test.status != TestStatus.DRAFT:
            return {"status": "error", "details": {"message": f"Test is {test.status.value}, cannot start"}}

        test.status = TestStatus.RUNNING
        test.started_at = datetime.now(timezone.utc).isoformat()

        return {
            "status": "success",
            "details": {"test_id": test_id, "status": "running"},
            "logs": [f"A/B test '{test.name}' started"],
        }

    def pause_test(self, test_id: str) -> dict:
        """Pause a running test."""
        test = self._tests.get(test_id)
        if not test:
            return {"status": "error", "details": {"message": "Test not found"}}
        test.status = TestStatus.PAUSED
        return {"status": "success", "details": {"test_id": test_id, "status": "paused"}}

    def stop_test(self, test_id: str) -> dict:
        """Stop and complete a test, declaring a winner if significant."""
        test = self._tests.get(test_id)
        if not test:
            return {"status": "error", "details": {"message": "Test not found"}}

        test.status = TestStatus.COMPLETED
        test.completed_at = datetime.now(timezone.utc).isoformat()

        # Determine winner
        analysis = self.analyse_test(test_id)
        return {
            "status": "success",
            "details": {
                "test_id": test_id,
                "status": "completed",
                "analysis": analysis.get("details", {}),
            },
            "logs": [f"A/B test '{test.name}' completed"],
        }

    # ---- Recording metrics -------------------------------------------------

    def record_event(self, test_id: str, variant_id: str,
                     event_type: str, count: int = 1,
                     revenue: float = 0.0) -> dict:
        """
        Record an event for a variant.

        Args:
            test_id: The test ID.
            variant_id: The variant ID.
            event_type: One of: send, open, click, conversion, unsubscribe.
            count: Number of events.
            revenue: Revenue amount (for conversion events).
        """
        test = self._tests.get(test_id)
        if not test:
            return {"status": "error", "details": {"message": "Test not found"}}

        variant = None
        for v in test.variants:
            if v.id == variant_id:
                variant = v
                break

        if not variant:
            return {"status": "error", "details": {"message": "Variant not found"}}

        if event_type == "send":
            variant.sends += count
        elif event_type == "open":
            variant.opens += count
        elif event_type == "click":
            variant.clicks += count
        elif event_type == "conversion":
            variant.conversions += count
            variant.revenue += revenue
        elif event_type == "unsubscribe":
            variant.unsubscribes += count

        # Check for auto-completion
        auto_result = self._check_auto_complete(test)

        return {
            "status": "success",
            "details": {
                "variant_id": variant_id,
                "event_type": event_type,
                "count": count,
                "auto_completed": auto_result.get("completed", False),
            },
        }

    def record_events_batch(self, test_id: str, events: list[dict]) -> dict:
        """Record multiple events at once."""
        results = []
        for event in events:
            result = self.record_event(
                test_id=test_id,
                variant_id=event["variant_id"],
                event_type=event["event_type"],
                count=event.get("count", 1),
                revenue=event.get("revenue", 0.0),
            )
            results.append(result)
        return {"status": "success", "details": {"events_recorded": len(results)}}

    # ---- Analysis ----------------------------------------------------------

    def analyse_test(self, test_id: str) -> dict:
        """
        Perform statistical analysis on a test.

        Compares each treatment variant against the control using a
        two-proportion z-test on the primary metric.
        """
        test = self._tests.get(test_id)
        if not test:
            return {"status": "error", "details": {"message": "Test not found"}}

        # Find control
        control = None
        treatments = []
        for v in test.variants:
            if v.is_control:
                control = v
            else:
                treatments.append(v)

        if not control:
            return {"status": "error", "details": {"message": "No control variant found"}}

        control_rate = control.get_metric(test.primary_metric)
        control_n = control.sends

        comparisons = []
        best_variant = control
        best_confidence = 0.0

        for treatment in treatments:
            treatment_rate = treatment.get_metric(test.primary_metric)
            treatment_n = treatment.sends

            # Statistical test
            z = self._calculator.z_score(control_rate, treatment_rate, control_n, treatment_n)
            p_val = self._calculator.p_value_from_z(z)
            confidence = self._calculator.confidence_level(p_val)
            lift = self._calculator.relative_lift(control_rate, treatment_rate)

            is_significant = confidence >= test.confidence_threshold
            has_enough_data = (control_n >= test.min_sample_per_variant and
                               treatment_n >= test.min_sample_per_variant)

            comparison = {
                "variant_id": treatment.id,
                "variant_name": treatment.name,
                "control_rate": round(control_rate, 4),
                "treatment_rate": round(treatment_rate, 4),
                "relative_lift": round(lift, 4),
                "z_score": round(z, 4),
                "p_value": round(p_val, 6),
                "confidence": round(confidence, 2),
                "is_significant": is_significant,
                "has_enough_data": has_enough_data,
                "samples_needed": test.min_sample_per_variant - min(control_n, treatment_n)
                                  if not has_enough_data else 0,
            }
            comparisons.append(comparison)

            if is_significant and treatment_rate > control_rate and confidence > best_confidence:
                best_variant = treatment
                best_confidence = confidence

        # Determine winner
        winner = None
        if best_variant != control and best_confidence >= test.confidence_threshold:
            winner = {
                "variant_id": best_variant.id,
                "variant_name": best_variant.name,
                "confidence": round(best_confidence, 2),
                "lift": round(
                    self._calculator.relative_lift(
                        control_rate, best_variant.get_metric(test.primary_metric)
                    ), 4
                ),
            }
            test.winner_variant_id = best_variant.id
            test.winner_confidence = best_confidence

        return {
            "status": "success",
            "details": {
                "test_id": test_id,
                "test_name": test.name,
                "primary_metric": test.primary_metric.value,
                "control": control.to_dict(),
                "comparisons": comparisons,
                "winner": winner,
                "is_conclusive": winner is not None,
                "total_sends": sum(v.sends for v in test.variants),
            },
        }

    def get_test(self, test_id: str) -> Optional[dict]:
        """Get a test with current state."""
        test = self._tests.get(test_id)
        if test:
            return test.to_dict()
        return None

    def list_tests(self, campaign_id: Optional[str] = None,
                   status: Optional[str] = None) -> list[dict]:
        """List all tests with optional filtering."""
        tests = list(self._tests.values())
        if campaign_id:
            tests = [t for t in tests if t.campaign_id == campaign_id]
        if status:
            tests = [t for t in tests if t.status.value == status]
        return [t.to_dict() for t in tests]

    def calculate_sample_size(
        self,
        baseline_rate: float,
        minimum_detectable_effect: float = 0.1,
        alpha: float = 0.05,
        power: float = 0.80,
    ) -> dict:
        """
        Calculate required sample size for a test.

        Args:
            baseline_rate: Current baseline rate for the metric.
            minimum_detectable_effect: Minimum relative effect to detect.
            alpha: Significance level.
            power: Statistical power.
        """
        sample_size = self._calculator.minimum_sample_size(
            baseline_rate, minimum_detectable_effect, alpha, power
        )
        return {
            "sample_size_per_variant": sample_size,
            "total_sample_size": sample_size * 2,
            "parameters": {
                "baseline_rate": baseline_rate,
                "minimum_detectable_effect": minimum_detectable_effect,
                "alpha": alpha,
                "power": power,
            },
        }

    # ---- Internal ----------------------------------------------------------

    def _check_auto_complete(self, test: ABTest) -> dict:
        """Check if a test should be auto-completed."""
        if test.status != TestStatus.RUNNING:
            return {"completed": False}

        # Check if all variants have enough data
        all_have_data = all(
            v.sends >= test.min_sample_per_variant for v in test.variants
        )
        if not all_have_data:
            return {"completed": False}

        # Check if we have a significant winner
        analysis = self.analyse_test(test.id)
        if analysis.get("details", {}).get("is_conclusive", False):
            test.status = TestStatus.COMPLETED
            test.completed_at = datetime.now(timezone.utc).isoformat()
            logger.info("A/B test '%s' auto-completed with winner", test.name)
            return {"completed": True}

        return {"completed": False}
