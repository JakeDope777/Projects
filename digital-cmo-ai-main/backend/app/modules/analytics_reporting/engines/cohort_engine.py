"""
Cohort Analysis Engine — Customer Retention & Behavior Tracking

Implements cohort analysis to track how groups of customers (cohorts)
behave over time. Supports:
  - Acquisition cohorts (grouped by signup month)
  - Behavioral cohorts (grouped by first action type)
  - Revenue cohorts (grouped by initial purchase value)

Outputs retention matrices, LTV curves, and cohort comparison data.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Optional

import numpy as np


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------

@dataclass
class CustomerEvent:
    """A single customer event for cohort analysis."""
    customer_id: str
    event_type: str  # "signup", "purchase", "login", "pageview", etc.
    timestamp: str  # ISO datetime
    revenue: float = 0.0
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class CohortDefinition:
    """Defines how to group customers into cohorts."""
    cohort_type: str = "acquisition"  # "acquisition", "behavioral", "revenue"
    period: str = "month"  # "week", "month", "quarter"
    retention_event: str = "purchase"  # Event that counts as "retained"
    num_periods: int = 12  # How many periods to track


@dataclass
class CohortResult:
    """Output of cohort analysis."""
    cohort_type: str
    period: str
    cohort_labels: list[str]
    retention_matrix: list[list[float]]  # Rows=cohorts, Cols=periods, Values=retention %
    cohort_sizes: list[int]
    avg_retention_by_period: list[float]
    ltv_by_cohort: list[float]
    revenue_matrix: list[list[float]]
    summary: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class CohortAnalysisEngine:
    """Perform cohort analysis on customer event data."""

    def analyze(
        self,
        events: list[CustomerEvent],
        definition: Optional[CohortDefinition] = None,
    ) -> CohortResult:
        """
        Run cohort analysis on customer events.

        Args:
            events: List of customer events.
            definition: Cohort configuration.

        Returns:
            CohortResult with retention matrix and metrics.
        """
        definition = definition or CohortDefinition()

        if definition.cohort_type == "acquisition":
            return self._acquisition_cohort(events, definition)
        elif definition.cohort_type == "behavioral":
            return self._behavioral_cohort(events, definition)
        elif definition.cohort_type == "revenue":
            return self._revenue_cohort(events, definition)
        else:
            return self._acquisition_cohort(events, definition)

    # ------------------------------------------------------------------
    # Acquisition Cohort
    # ------------------------------------------------------------------

    def _acquisition_cohort(
        self,
        events: list[CustomerEvent],
        defn: CohortDefinition,
    ) -> CohortResult:
        """Group customers by their signup/first-event period."""
        # Find first event per customer (signup)
        first_event: dict[str, datetime] = {}
        for e in events:
            ts = self._parse_ts(e.timestamp)
            cid = e.customer_id
            if cid not in first_event or ts < first_event[cid]:
                first_event[cid] = ts

        # Assign customers to cohorts
        cohort_map: dict[str, str] = {}  # customer_id -> cohort_label
        for cid, ts in first_event.items():
            cohort_map[cid] = self._period_label(ts, defn.period)

        # Build retention matrix
        return self._build_retention(events, cohort_map, defn)

    # ------------------------------------------------------------------
    # Behavioral Cohort
    # ------------------------------------------------------------------

    def _behavioral_cohort(
        self,
        events: list[CustomerEvent],
        defn: CohortDefinition,
    ) -> CohortResult:
        """Group customers by their first action type."""
        first_action: dict[str, str] = {}
        first_time: dict[str, datetime] = {}
        for e in events:
            ts = self._parse_ts(e.timestamp)
            cid = e.customer_id
            if cid not in first_time or ts < first_time[cid]:
                first_time[cid] = ts
                first_action[cid] = e.event_type

        cohort_map = {cid: action for cid, action in first_action.items()}
        return self._build_retention(events, cohort_map, defn)

    # ------------------------------------------------------------------
    # Revenue Cohort
    # ------------------------------------------------------------------

    def _revenue_cohort(
        self,
        events: list[CustomerEvent],
        defn: CohortDefinition,
    ) -> CohortResult:
        """Group customers by their initial purchase value tier."""
        first_purchase: dict[str, float] = {}
        first_time: dict[str, datetime] = {}

        for e in events:
            if e.revenue <= 0:
                continue
            ts = self._parse_ts(e.timestamp)
            cid = e.customer_id
            if cid not in first_time or ts < first_time[cid]:
                first_time[cid] = ts
                first_purchase[cid] = e.revenue

        # Tier assignment
        cohort_map: dict[str, str] = {}
        for cid, rev in first_purchase.items():
            if rev < 50:
                cohort_map[cid] = "$0-$49"
            elif rev < 100:
                cohort_map[cid] = "$50-$99"
            elif rev < 250:
                cohort_map[cid] = "$100-$249"
            elif rev < 500:
                cohort_map[cid] = "$250-$499"
            else:
                cohort_map[cid] = "$500+"

        # Include non-purchasers
        all_customers = {e.customer_id for e in events}
        for cid in all_customers:
            if cid not in cohort_map:
                cohort_map[cid] = "No purchase"

        return self._build_retention(events, cohort_map, defn)

    # ------------------------------------------------------------------
    # Shared retention matrix builder
    # ------------------------------------------------------------------

    def _build_retention(
        self,
        events: list[CustomerEvent],
        cohort_map: dict[str, str],
        defn: CohortDefinition,
    ) -> CohortResult:
        """Build the retention and revenue matrices from events and cohort assignments."""
        # Find the first event timestamp per customer for period offset calculation
        first_ts: dict[str, datetime] = {}
        for e in events:
            ts = self._parse_ts(e.timestamp)
            cid = e.customer_id
            if cid not in first_ts or ts < first_ts[cid]:
                first_ts[cid] = ts

        # Organize events by cohort and period offset
        cohort_labels_set: set[str] = set(cohort_map.values())
        cohort_labels = sorted(cohort_labels_set)

        # For each cohort, track which customers are active in each period
        # and revenue per period
        cohort_data: dict[str, dict[int, set[str]]] = {
            label: defaultdict(set) for label in cohort_labels
        }
        cohort_revenue: dict[str, dict[int, float]] = {
            label: defaultdict(float) for label in cohort_labels
        }

        for e in events:
            cid = e.customer_id
            if cid not in cohort_map:
                continue
            label = cohort_map[cid]
            ts = self._parse_ts(e.timestamp)
            base = first_ts.get(cid, ts)
            period_offset = self._period_offset(base, ts, defn.period)

            if 0 <= period_offset < defn.num_periods:
                # Count retention event or any event
                if defn.retention_event == "any" or e.event_type == defn.retention_event:
                    cohort_data[label][period_offset].add(cid)
                cohort_revenue[label][period_offset] += e.revenue

        # Build matrices
        cohort_sizes = []
        retention_matrix = []
        revenue_matrix = []
        ltv_by_cohort = []

        for label in cohort_labels:
            # Cohort size = customers in period 0
            size = len(cohort_data[label].get(0, set()))
            if size == 0:
                # Use total customers in this cohort
                size = sum(1 for cid, lbl in cohort_map.items() if lbl == label)
            cohort_sizes.append(size)

            row = []
            rev_row = []
            cumulative_rev = 0.0
            for p in range(defn.num_periods):
                active = len(cohort_data[label].get(p, set()))
                retention = round((active / max(size, 1)) * 100, 1)
                row.append(retention)
                period_rev = round(cohort_revenue[label].get(p, 0.0), 2)
                rev_row.append(period_rev)
                cumulative_rev += period_rev

            retention_matrix.append(row)
            revenue_matrix.append(rev_row)
            ltv_by_cohort.append(round(cumulative_rev / max(size, 1), 2))

        # Average retention by period
        avg_retention = []
        for p in range(defn.num_periods):
            vals = [retention_matrix[i][p] for i in range(len(cohort_labels)) if cohort_sizes[i] > 0]
            avg_retention.append(round(np.mean(vals), 1) if vals else 0.0)

        # Summary statistics
        overall_retention_m1 = avg_retention[1] if len(avg_retention) > 1 else 0.0
        best_cohort_idx = (
            max(range(len(ltv_by_cohort)), key=lambda i: ltv_by_cohort[i])
            if ltv_by_cohort else 0
        )

        summary = {
            "total_customers": len(cohort_map),
            "total_cohorts": len(cohort_labels),
            "avg_period_1_retention": overall_retention_m1,
            "best_cohort": cohort_labels[best_cohort_idx] if cohort_labels else "",
            "best_cohort_ltv": ltv_by_cohort[best_cohort_idx] if ltv_by_cohort else 0.0,
            "avg_ltv": round(np.mean(ltv_by_cohort), 2) if ltv_by_cohort else 0.0,
        }

        return CohortResult(
            cohort_type=defn.cohort_type,
            period=defn.period,
            cohort_labels=cohort_labels,
            retention_matrix=retention_matrix,
            cohort_sizes=cohort_sizes,
            avg_retention_by_period=avg_retention,
            ltv_by_cohort=ltv_by_cohort,
            revenue_matrix=revenue_matrix,
            summary=summary,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_ts(ts_str: str) -> datetime:
        for fmt in (
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
        ):
            try:
                return datetime.strptime(ts_str, fmt)
            except ValueError:
                continue
        return datetime.now()

    @staticmethod
    def _period_label(dt: datetime, period: str) -> str:
        if period == "week":
            iso = dt.isocalendar()
            return f"{iso[0]}-W{iso[1]:02d}"
        elif period == "month":
            return dt.strftime("%Y-%m")
        elif period == "quarter":
            q = (dt.month - 1) // 3 + 1
            return f"{dt.year}-Q{q}"
        return dt.strftime("%Y-%m")

    @staticmethod
    def _period_offset(base: datetime, current: datetime, period: str) -> int:
        delta = current - base
        days = delta.days
        if period == "week":
            return days // 7
        elif period == "month":
            return (current.year - base.year) * 12 + (current.month - base.month)
        elif period == "quarter":
            base_q = (base.year * 4) + (base.month - 1) // 3
            curr_q = (current.year * 4) + (current.month - 1) // 3
            return curr_q - base_q
        return days // 30
