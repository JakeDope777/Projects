"""
Attribution Engine — Multi-Touch Attribution Modeling

Implements five attribution models:
  1. First-Touch: 100% credit to the first touchpoint
  2. Last-Touch: 100% credit to the last touchpoint
  3. Linear: Equal credit across all touchpoints
  4. Time-Decay: Exponentially more credit to recent touchpoints
  5. Data-Driven (Shapley Value approximation): Credit based on marginal contribution

Each model takes a list of customer journeys (sequences of touchpoints)
and returns channel-level attribution scores.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field
from itertools import combinations
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------

@dataclass
class Touchpoint:
    """A single interaction in a customer journey."""
    channel: str
    timestamp: str  # ISO datetime string
    campaign_id: Optional[str] = None
    cost: float = 0.0


@dataclass
class CustomerJourney:
    """A customer's full path from first touch to conversion."""
    customer_id: str
    touchpoints: list[Touchpoint]
    converted: bool = False
    conversion_value: float = 0.0


@dataclass
class AttributionResult:
    """Attribution output for a single model."""
    model: str
    channel_scores: dict[str, float]  # channel -> attributed value
    channel_conversions: dict[str, float]  # channel -> attributed conversions
    channel_cost: dict[str, float]  # channel -> total cost
    channel_roas: dict[str, float]  # channel -> return on ad spend
    total_conversions: int = 0
    total_value: float = 0.0


# ---------------------------------------------------------------------------
# Attribution Engine
# ---------------------------------------------------------------------------

class AttributionEngine:
    """Compute multi-touch attribution across five models."""

    SUPPORTED_MODELS = [
        "first_touch",
        "last_touch",
        "linear",
        "time_decay",
        "data_driven",
    ]

    def attribute(
        self,
        journeys: list[CustomerJourney],
        model: str = "linear",
        decay_half_life_days: float = 7.0,
    ) -> AttributionResult:
        """
        Run attribution on a list of customer journeys.

        Args:
            journeys: List of CustomerJourney objects.
            model: Attribution model name.
            decay_half_life_days: Half-life for time-decay model (in days).

        Returns:
            AttributionResult with channel-level scores.
        """
        dispatch = {
            "first_touch": self._first_touch,
            "last_touch": self._last_touch,
            "linear": self._linear,
            "time_decay": self._time_decay,
            "data_driven": self._data_driven,
        }

        fn = dispatch.get(model, self._linear)
        return fn(journeys, decay_half_life_days)

    def attribute_all_models(
        self,
        journeys: list[CustomerJourney],
        decay_half_life_days: float = 7.0,
    ) -> dict[str, AttributionResult]:
        """Run all five attribution models and return results keyed by model name."""
        return {
            m: self.attribute(journeys, model=m, decay_half_life_days=decay_half_life_days)
            for m in self.SUPPORTED_MODELS
        }

    # ------------------------------------------------------------------
    # First-Touch Attribution
    # ------------------------------------------------------------------

    def _first_touch(
        self,
        journeys: list[CustomerJourney],
        _half_life: float,
    ) -> AttributionResult:
        scores: dict[str, float] = defaultdict(float)
        conv_counts: dict[str, float] = defaultdict(float)
        costs: dict[str, float] = defaultdict(float)

        converted_journeys = [j for j in journeys if j.converted and j.touchpoints]
        for j in converted_journeys:
            first = j.touchpoints[0]
            scores[first.channel] += j.conversion_value
            conv_counts[first.channel] += 1.0

        # Aggregate costs from all journeys
        for j in journeys:
            for tp in j.touchpoints:
                costs[tp.channel] += tp.cost

        return self._build_result("first_touch", scores, conv_counts, costs, journeys)

    # ------------------------------------------------------------------
    # Last-Touch Attribution
    # ------------------------------------------------------------------

    def _last_touch(
        self,
        journeys: list[CustomerJourney],
        _half_life: float,
    ) -> AttributionResult:
        scores: dict[str, float] = defaultdict(float)
        conv_counts: dict[str, float] = defaultdict(float)
        costs: dict[str, float] = defaultdict(float)

        converted_journeys = [j for j in journeys if j.converted and j.touchpoints]
        for j in converted_journeys:
            last = j.touchpoints[-1]
            scores[last.channel] += j.conversion_value
            conv_counts[last.channel] += 1.0

        for j in journeys:
            for tp in j.touchpoints:
                costs[tp.channel] += tp.cost

        return self._build_result("last_touch", scores, conv_counts, costs, journeys)

    # ------------------------------------------------------------------
    # Linear Attribution
    # ------------------------------------------------------------------

    def _linear(
        self,
        journeys: list[CustomerJourney],
        _half_life: float,
    ) -> AttributionResult:
        scores: dict[str, float] = defaultdict(float)
        conv_counts: dict[str, float] = defaultdict(float)
        costs: dict[str, float] = defaultdict(float)

        converted_journeys = [j for j in journeys if j.converted and j.touchpoints]
        for j in converted_journeys:
            n = len(j.touchpoints)
            share = 1.0 / n
            for tp in j.touchpoints:
                scores[tp.channel] += j.conversion_value * share
                conv_counts[tp.channel] += share

        for j in journeys:
            for tp in j.touchpoints:
                costs[tp.channel] += tp.cost

        return self._build_result("linear", scores, conv_counts, costs, journeys)

    # ------------------------------------------------------------------
    # Time-Decay Attribution
    # ------------------------------------------------------------------

    def _time_decay(
        self,
        journeys: list[CustomerJourney],
        half_life_days: float,
    ) -> AttributionResult:
        scores: dict[str, float] = defaultdict(float)
        conv_counts: dict[str, float] = defaultdict(float)
        costs: dict[str, float] = defaultdict(float)
        decay_rate = math.log(2) / max(half_life_days, 0.1)

        converted_journeys = [j for j in journeys if j.converted and j.touchpoints]
        for j in converted_journeys:
            tps = j.touchpoints
            if not tps:
                continue

            # Parse timestamps and compute weights
            last_ts = self._parse_ts(tps[-1].timestamp)
            weights = []
            for tp in tps:
                ts = self._parse_ts(tp.timestamp)
                days_before = max((last_ts - ts).total_seconds() / 86400, 0)
                w = math.exp(-decay_rate * days_before)
                weights.append(w)

            total_w = sum(weights) or 1.0
            for tp, w in zip(tps, weights):
                share = w / total_w
                scores[tp.channel] += j.conversion_value * share
                conv_counts[tp.channel] += share

        for j in journeys:
            for tp in j.touchpoints:
                costs[tp.channel] += tp.cost

        return self._build_result("time_decay", scores, conv_counts, costs, journeys)

    # ------------------------------------------------------------------
    # Data-Driven Attribution (Shapley Value Approximation)
    # ------------------------------------------------------------------

    def _data_driven(
        self,
        journeys: list[CustomerJourney],
        _half_life: float,
    ) -> AttributionResult:
        """
        Approximate Shapley values by computing marginal contributions
        of each channel across all observed coalitions.
        """
        scores: dict[str, float] = defaultdict(float)
        conv_counts: dict[str, float] = defaultdict(float)
        costs: dict[str, float] = defaultdict(float)

        # Build coalition → conversion rate mapping
        coalition_stats: dict[frozenset[str], dict] = defaultdict(
            lambda: {"conversions": 0, "total": 0, "value": 0.0}
        )
        all_channels: set[str] = set()

        for j in journeys:
            channels_in_journey = frozenset(tp.channel for tp in j.touchpoints)
            all_channels.update(channels_in_journey)
            coalition_stats[channels_in_journey]["total"] += 1
            if j.converted:
                coalition_stats[channels_in_journey]["conversions"] += 1
                coalition_stats[channels_in_journey]["value"] += j.conversion_value

        # Compute Shapley values
        channels = sorted(all_channels)
        n = len(channels)

        for channel in channels:
            shapley_value = 0.0
            shapley_conv = 0.0
            others = [c for c in channels if c != channel]

            # Iterate over all subsets of other channels
            for size in range(len(others) + 1):
                for subset in combinations(others, size):
                    coalition_without = frozenset(subset)
                    coalition_with = frozenset(subset) | {channel}

                    # Get conversion rates
                    stats_with = coalition_stats.get(coalition_with)
                    stats_without = coalition_stats.get(coalition_without)

                    rate_with = (
                        stats_with["value"] / max(stats_with["total"], 1)
                        if stats_with and stats_with["total"] > 0
                        else 0.0
                    )
                    rate_without = (
                        stats_without["value"] / max(stats_without["total"], 1)
                        if stats_without and stats_without["total"] > 0
                        else 0.0
                    )

                    conv_with = (
                        stats_with["conversions"] / max(stats_with["total"], 1)
                        if stats_with and stats_with["total"] > 0
                        else 0.0
                    )
                    conv_without = (
                        stats_without["conversions"] / max(stats_without["total"], 1)
                        if stats_without and stats_without["total"] > 0
                        else 0.0
                    )

                    marginal = rate_with - rate_without
                    marginal_conv = conv_with - conv_without

                    # Shapley weight
                    s = len(subset)
                    weight = (
                        math.factorial(s) * math.factorial(n - s - 1)
                    ) / math.factorial(n)

                    shapley_value += weight * marginal
                    shapley_conv += weight * marginal_conv

            scores[channel] = max(shapley_value, 0)
            conv_counts[channel] = max(shapley_conv, 0)

        # Normalize to total conversion value
        total_value = sum(j.conversion_value for j in journeys if j.converted)
        score_sum = sum(scores.values()) or 1.0
        for ch in scores:
            scores[ch] = (scores[ch] / score_sum) * total_value

        total_conv = sum(1 for j in journeys if j.converted)
        conv_sum = sum(conv_counts.values()) or 1.0
        for ch in conv_counts:
            conv_counts[ch] = (conv_counts[ch] / conv_sum) * total_conv

        for j in journeys:
            for tp in j.touchpoints:
                costs[tp.channel] += tp.cost

        return self._build_result("data_driven", scores, conv_counts, costs, journeys)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_result(
        model: str,
        scores: dict[str, float],
        conv_counts: dict[str, float],
        costs: dict[str, float],
        journeys: list[CustomerJourney],
    ) -> AttributionResult:
        channel_roas = {}
        for ch in scores:
            cost = costs.get(ch, 0)
            channel_roas[ch] = round(scores[ch] / cost, 2) if cost > 0 else 0.0

        return AttributionResult(
            model=model,
            channel_scores={k: round(v, 2) for k, v in scores.items()},
            channel_conversions={k: round(v, 2) for k, v in conv_counts.items()},
            channel_cost={k: round(v, 2) for k, v in costs.items()},
            channel_roas=channel_roas,
            total_conversions=sum(1 for j in journeys if j.converted),
            total_value=round(sum(j.conversion_value for j in journeys if j.converted), 2),
        )

    @staticmethod
    def _parse_ts(ts_str: str):
        """Parse an ISO timestamp string."""
        from datetime import datetime, timezone

        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(ts_str, fmt)
            except ValueError:
                continue
        # Fallback
        return datetime.now(timezone.utc)
