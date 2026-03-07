"""
Anomaly Detection Engine — Metric Deviation Alerts

Detects anomalies in marketing metrics using multiple methods:
  1. Z-Score: Flag values beyond N standard deviations
  2. IQR (Interquartile Range): Robust outlier detection
  3. Moving Average Deviation: Detect sudden shifts from rolling trend
  4. Percentage Change: Alert on large period-over-period changes

Generates alerts with severity levels and contextual explanations.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

import numpy as np


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------

@dataclass
class Anomaly:
    """A detected anomaly in a metric."""
    metric: str
    current_value: float
    expected_value: float
    deviation: float  # How far from expected (in std devs or %)
    severity: str  # "info", "warning", "critical"
    method: str  # Detection method used
    direction: str  # "above" or "below"
    message: str
    timestamp: str = ""


@dataclass
class AnomalyReport:
    """Collection of detected anomalies."""
    anomalies: list[Anomaly]
    total_metrics_checked: int = 0
    anomaly_count: int = 0
    critical_count: int = 0
    warning_count: int = 0
    generated_at: str = ""


# ---------------------------------------------------------------------------
# Thresholds configuration
# ---------------------------------------------------------------------------

@dataclass
class AnomalyThresholds:
    """Configurable thresholds for anomaly detection."""
    z_score_warning: float = 2.0
    z_score_critical: float = 3.0
    iqr_multiplier: float = 1.5
    pct_change_warning: float = 30.0  # %
    pct_change_critical: float = 50.0  # %
    ma_deviation_warning: float = 2.0  # std devs
    ma_deviation_critical: float = 3.0  # std devs
    min_data_points: int = 7  # Minimum historical points needed


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class AnomalyDetectionEngine:
    """Detect anomalies in marketing metrics."""

    def __init__(self, thresholds: Optional[AnomalyThresholds] = None):
        self.thresholds = thresholds or AnomalyThresholds()

    def detect_anomalies(
        self,
        current_metrics: dict[str, float],
        historical_metrics: list[dict[str, float]],
        methods: Optional[list[str]] = None,
    ) -> AnomalyReport:
        """
        Detect anomalies by comparing current metrics against historical data.

        Args:
            current_metrics: Current period's metric values.
            historical_metrics: List of past period metric dicts (oldest first).
            methods: Detection methods to use. Defaults to all.

        Returns:
            AnomalyReport with detected anomalies.
        """
        methods = methods or ["z_score", "iqr", "moving_average", "pct_change"]
        anomalies: list[Anomaly] = []
        metrics_checked = 0

        for metric_name, current_value in current_metrics.items():
            if not isinstance(current_value, (int, float)):
                continue

            # Extract historical values for this metric
            hist_values = []
            for period in historical_metrics:
                val = period.get(metric_name)
                if isinstance(val, (int, float)):
                    hist_values.append(float(val))

            if len(hist_values) < self.thresholds.min_data_points:
                continue

            metrics_checked += 1
            current_float = float(current_value)

            if "z_score" in methods:
                anomaly = self._z_score_check(metric_name, current_float, hist_values)
                if anomaly:
                    anomalies.append(anomaly)

            if "iqr" in methods:
                anomaly = self._iqr_check(metric_name, current_float, hist_values)
                if anomaly:
                    anomalies.append(anomaly)

            if "moving_average" in methods:
                anomaly = self._moving_average_check(metric_name, current_float, hist_values)
                if anomaly:
                    anomalies.append(anomaly)

            if "pct_change" in methods and len(hist_values) >= 1:
                anomaly = self._pct_change_check(metric_name, current_float, hist_values[-1])
                if anomaly:
                    anomalies.append(anomaly)

        # Deduplicate: keep highest severity per metric
        anomalies = self._deduplicate(anomalies)

        now = datetime.now(timezone.utc).isoformat()
        return AnomalyReport(
            anomalies=anomalies,
            total_metrics_checked=metrics_checked,
            anomaly_count=len(anomalies),
            critical_count=sum(1 for a in anomalies if a.severity == "critical"),
            warning_count=sum(1 for a in anomalies if a.severity == "warning"),
            generated_at=now,
        )

    # ------------------------------------------------------------------
    # Z-Score Detection
    # ------------------------------------------------------------------

    def _z_score_check(
        self,
        metric: str,
        current: float,
        history: list[float],
    ) -> Optional[Anomaly]:
        mean = np.mean(history)
        std = np.std(history)
        if std == 0:
            return None

        z = abs(current - mean) / std
        direction = "above" if current > mean else "below"

        if z >= self.thresholds.z_score_critical:
            severity = "critical"
        elif z >= self.thresholds.z_score_warning:
            severity = "warning"
        else:
            return None

        return Anomaly(
            metric=metric,
            current_value=round(current, 2),
            expected_value=round(float(mean), 2),
            deviation=round(float(z), 2),
            severity=severity,
            method="z_score",
            direction=direction,
            message=(
                f"{metric} is {round(float(z), 1)} standard deviations {direction} "
                f"the historical mean ({round(float(mean), 2)}). "
                f"Current value: {round(current, 2)}."
            ),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    # ------------------------------------------------------------------
    # IQR Detection
    # ------------------------------------------------------------------

    def _iqr_check(
        self,
        metric: str,
        current: float,
        history: list[float],
    ) -> Optional[Anomaly]:
        q1 = float(np.percentile(history, 25))
        q3 = float(np.percentile(history, 75))
        iqr = q3 - q1
        if iqr == 0:
            return None

        lower = q1 - self.thresholds.iqr_multiplier * iqr
        upper = q3 + self.thresholds.iqr_multiplier * iqr

        if current < lower:
            direction = "below"
            deviation = (lower - current) / iqr
        elif current > upper:
            direction = "above"
            deviation = (current - upper) / iqr
        else:
            return None

        severity = "critical" if deviation > 2.0 else "warning"

        return Anomaly(
            metric=metric,
            current_value=round(current, 2),
            expected_value=round((q1 + q3) / 2, 2),
            deviation=round(deviation, 2),
            severity=severity,
            method="iqr",
            direction=direction,
            message=(
                f"{metric} ({round(current, 2)}) is {direction} the IQR bounds "
                f"[{round(lower, 2)}, {round(upper, 2)}]. "
                f"This is an outlier by {round(deviation, 1)}x IQR."
            ),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    # ------------------------------------------------------------------
    # Moving Average Deviation
    # ------------------------------------------------------------------

    def _moving_average_check(
        self,
        metric: str,
        current: float,
        history: list[float],
    ) -> Optional[Anomaly]:
        window = min(7, len(history))
        recent = history[-window:]
        ma = np.mean(recent)
        std = np.std(recent)
        if std == 0:
            return None

        deviation = abs(current - ma) / std
        direction = "above" if current > ma else "below"

        if deviation >= self.thresholds.ma_deviation_critical:
            severity = "critical"
        elif deviation >= self.thresholds.ma_deviation_warning:
            severity = "warning"
        else:
            return None

        return Anomaly(
            metric=metric,
            current_value=round(current, 2),
            expected_value=round(float(ma), 2),
            deviation=round(float(deviation), 2),
            severity=severity,
            method="moving_average",
            direction=direction,
            message=(
                f"{metric} deviates {round(float(deviation), 1)} std devs from its "
                f"{window}-period moving average ({round(float(ma), 2)}). "
                f"Current: {round(current, 2)}."
            ),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    # ------------------------------------------------------------------
    # Percentage Change Detection
    # ------------------------------------------------------------------

    def _pct_change_check(
        self,
        metric: str,
        current: float,
        previous: float,
    ) -> Optional[Anomaly]:
        if previous == 0:
            return None

        pct_change = ((current - previous) / abs(previous)) * 100
        direction = "above" if pct_change > 0 else "below"
        abs_change = abs(pct_change)

        if abs_change >= self.thresholds.pct_change_critical:
            severity = "critical"
        elif abs_change >= self.thresholds.pct_change_warning:
            severity = "warning"
        else:
            return None

        return Anomaly(
            metric=metric,
            current_value=round(current, 2),
            expected_value=round(previous, 2),
            deviation=round(pct_change, 1),
            severity=severity,
            method="pct_change",
            direction=direction,
            message=(
                f"{metric} changed by {round(pct_change, 1)}% compared to the previous period "
                f"(from {round(previous, 2)} to {round(current, 2)})."
            ),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _deduplicate(anomalies: list[Anomaly]) -> list[Anomaly]:
        """Keep only the highest-severity anomaly per metric."""
        severity_rank = {"critical": 3, "warning": 2, "info": 1}
        best: dict[str, Anomaly] = {}
        for a in anomalies:
            existing = best.get(a.metric)
            if existing is None or severity_rank.get(a.severity, 0) > severity_rank.get(existing.severity, 0):
                best[a.metric] = a
        return sorted(best.values(), key=lambda x: severity_rank.get(x.severity, 0), reverse=True)
