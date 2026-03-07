"""
Forecasting Engine — Time-Series Forecasting for Marketing Metrics

Implements multiple forecasting methods:
  - Simple Moving Average (baseline)
  - Exponential Smoothing (Holt-Winters)
  - ARIMA (Auto-Regressive Integrated Moving Average)
  - Linear Trend with Seasonality

Supports forecasting for revenue, leads, campaign performance, and any
numeric time-series metric.
"""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import numpy as np
import pandas as pd

# Optional: statsmodels for ARIMA (graceful fallback)
try:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    from statsmodels.tsa.arima.model import ARIMA

    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------

@dataclass
class TimeSeriesPoint:
    date: str  # ISO date string YYYY-MM-DD
    value: float


@dataclass
class ForecastResult:
    metric: str
    method: str
    horizon_days: int
    historical: list[dict[str, Any]]
    predictions: list[dict[str, Any]]
    model_diagnostics: dict[str, Any] = field(default_factory=dict)
    confidence_level: float = 0.95


# ---------------------------------------------------------------------------
# Forecasting Engine
# ---------------------------------------------------------------------------

class ForecastingEngine:
    """Multi-method time-series forecasting engine."""

    SUPPORTED_METHODS = [
        "auto",
        "moving_average",
        "holt_winters",
        "arima",
        "linear_trend",
    ]

    def forecast(
        self,
        metric_name: str,
        historical_data: list[TimeSeriesPoint],
        horizon: int = 30,
        method: str = "auto",
        confidence_level: float = 0.95,
        seasonal_period: int = 7,
    ) -> ForecastResult:
        """
        Generate a forecast for the given metric.

        Args:
            metric_name: Name of the metric being forecast.
            historical_data: List of TimeSeriesPoint with date and value.
            horizon: Number of days to forecast.
            method: Forecasting method to use.
            confidence_level: Confidence level for prediction intervals.
            seasonal_period: Seasonality period (7 for weekly, 30 for monthly).

        Returns:
            ForecastResult with predictions and diagnostics.
        """
        if not historical_data or len(historical_data) < 3:
            return self._fallback_forecast(metric_name, historical_data, horizon)

        if method == "auto":
            method = self._select_best_method(historical_data, seasonal_period)

        dispatch = {
            "moving_average": self._moving_average_forecast,
            "holt_winters": self._holt_winters_forecast,
            "arima": self._arima_forecast,
            "linear_trend": self._linear_trend_forecast,
        }

        fn = dispatch.get(method, self._linear_trend_forecast)
        return fn(
            metric_name,
            historical_data,
            horizon,
            confidence_level,
            seasonal_period,
        )

    # ------------------------------------------------------------------
    # Method selection
    # ------------------------------------------------------------------

    def _select_best_method(
        self,
        data: list[TimeSeriesPoint],
        seasonal_period: int,
    ) -> str:
        """Heuristically select the best method based on data characteristics."""
        n = len(data)
        if n < 14:
            return "linear_trend"
        if not HAS_STATSMODELS:
            return "moving_average" if n >= 7 else "linear_trend"
        if n >= 2 * seasonal_period:
            return "holt_winters"
        if n >= 30:
            return "arima"
        return "linear_trend"

    # ------------------------------------------------------------------
    # Moving Average
    # ------------------------------------------------------------------

    def _moving_average_forecast(
        self,
        metric: str,
        data: list[TimeSeriesPoint],
        horizon: int,
        confidence: float,
        seasonal_period: int,
    ) -> ForecastResult:
        values = np.array([p.value for p in data])
        window = min(7, len(values))
        ma = float(np.mean(values[-window:]))
        std = float(np.std(values[-window:])) if window > 1 else ma * 0.1
        z = self._z_score(confidence)

        last_date = datetime.strptime(data[-1].date, "%Y-%m-%d")
        predictions = []
        for i in range(1, horizon + 1):
            d = last_date + timedelta(days=i)
            predictions.append({
                "date": d.strftime("%Y-%m-%d"),
                "predicted": round(ma, 2),
                "lower_bound": round(ma - z * std * math.sqrt(i / window), 2),
                "upper_bound": round(ma + z * std * math.sqrt(i / window), 2),
            })

        return ForecastResult(
            metric=metric,
            method="moving_average",
            horizon_days=horizon,
            historical=[{"date": p.date, "value": p.value} for p in data[-14:]],
            predictions=predictions,
            model_diagnostics={"window": window, "mean": round(ma, 2), "std": round(std, 2)},
            confidence_level=confidence,
        )

    # ------------------------------------------------------------------
    # Holt-Winters Exponential Smoothing
    # ------------------------------------------------------------------

    def _holt_winters_forecast(
        self,
        metric: str,
        data: list[TimeSeriesPoint],
        horizon: int,
        confidence: float,
        seasonal_period: int,
    ) -> ForecastResult:
        if not HAS_STATSMODELS:
            return self._moving_average_forecast(metric, data, horizon, confidence, seasonal_period)

        values = np.array([p.value for p in data], dtype=float)
        # Ensure positive values for multiplicative seasonality
        values = np.maximum(values, 0.01)

        try:
            seasonal = "add" if np.any(values <= 0) else "mul"
            sp = min(seasonal_period, len(values) // 2)
            if sp < 2:
                sp = 2

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                model = ExponentialSmoothing(
                    values,
                    trend="add",
                    seasonal=seasonal,
                    seasonal_periods=sp,
                    initialization_method="estimated",
                ).fit(optimized=True)

            fc = model.forecast(horizon)
            residuals = model.resid
            std = float(np.std(residuals))
        except Exception:
            return self._linear_trend_forecast(metric, data, horizon, confidence, seasonal_period)

        z = self._z_score(confidence)
        last_date = datetime.strptime(data[-1].date, "%Y-%m-%d")
        predictions = []
        for i in range(horizon):
            d = last_date + timedelta(days=i + 1)
            pred = float(fc[i]) if not np.isnan(fc[i]) else float(values[-1])
            predictions.append({
                "date": d.strftime("%Y-%m-%d"),
                "predicted": round(pred, 2),
                "lower_bound": round(pred - z * std * math.sqrt(i + 1), 2),
                "upper_bound": round(pred + z * std * math.sqrt(i + 1), 2),
            })

        return ForecastResult(
            metric=metric,
            method="holt_winters",
            horizon_days=horizon,
            historical=[{"date": p.date, "value": p.value} for p in data[-14:]],
            predictions=predictions,
            model_diagnostics={
                "aic": round(model.aic, 2) if hasattr(model, "aic") else None,
                "seasonal_period": sp,
                "seasonal_type": seasonal,
                "residual_std": round(std, 2),
            },
            confidence_level=confidence,
        )

    # ------------------------------------------------------------------
    # ARIMA
    # ------------------------------------------------------------------

    def _arima_forecast(
        self,
        metric: str,
        data: list[TimeSeriesPoint],
        horizon: int,
        confidence: float,
        seasonal_period: int,
    ) -> ForecastResult:
        if not HAS_STATSMODELS:
            return self._moving_average_forecast(metric, data, horizon, confidence, seasonal_period)

        values = np.array([p.value for p in data], dtype=float)

        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                # Use auto-order selection heuristic
                order = self._select_arima_order(values)
                model = ARIMA(values, order=order).fit()
                fc_result = model.get_forecast(steps=horizon)
                fc_mean = fc_result.predicted_mean
                fc_ci = fc_result.conf_int(alpha=1 - confidence)
        except Exception:
            return self._linear_trend_forecast(metric, data, horizon, confidence, seasonal_period)

        last_date = datetime.strptime(data[-1].date, "%Y-%m-%d")
        predictions = []
        for i in range(horizon):
            d = last_date + timedelta(days=i + 1)
            try:
                raw_pred = float(fc_mean.iloc[i]) if hasattr(fc_mean, 'iloc') else float(fc_mean[i])
            except (IndexError, ValueError):
                raw_pred = float(values[-1])
            pred = raw_pred if not np.isnan(raw_pred) else float(values[-1])
            try:
                if hasattr(fc_ci, 'iloc'):
                    raw_lb = float(fc_ci.iloc[i, 0])
                    raw_ub = float(fc_ci.iloc[i, 1])
                else:
                    raw_lb = float(fc_ci[i, 0])
                    raw_ub = float(fc_ci[i, 1])
            except (IndexError, ValueError):
                raw_lb = pred * 0.8
                raw_ub = pred * 1.2
            lb = raw_lb if not np.isnan(raw_lb) else pred * 0.8
            ub = raw_ub if not np.isnan(raw_ub) else pred * 1.2
            predictions.append({
                "date": d.strftime("%Y-%m-%d"),
                "predicted": round(pred, 2),
                "lower_bound": round(lb, 2),
                "upper_bound": round(ub, 2),
            })

        return ForecastResult(
            metric=metric,
            method="arima",
            horizon_days=horizon,
            historical=[{"date": p.date, "value": p.value} for p in data[-14:]],
            predictions=predictions,
            model_diagnostics={
                "order": list(order),
                "aic": round(model.aic, 2),
                "bic": round(model.bic, 2),
            },
            confidence_level=confidence,
        )

    @staticmethod
    def _select_arima_order(values: np.ndarray) -> tuple[int, int, int]:
        """Simple heuristic for ARIMA order selection."""
        n = len(values)
        # Check stationarity via simple diff variance test
        diff1 = np.diff(values)
        if np.std(diff1) < np.std(values) * 0.7:
            d = 1
        else:
            d = 0
        p = min(2, n // 10)
        q = min(2, n // 10)
        return (max(p, 1), d, max(q, 1))

    # ------------------------------------------------------------------
    # Linear Trend with Seasonality
    # ------------------------------------------------------------------

    def _linear_trend_forecast(
        self,
        metric: str,
        data: list[TimeSeriesPoint],
        horizon: int,
        confidence: float,
        seasonal_period: int,
    ) -> ForecastResult:
        values = np.array([p.value for p in data], dtype=float)
        n = len(values)
        x = np.arange(n, dtype=float)

        # Fit linear trend
        slope, intercept = np.polyfit(x, values, 1) if n > 1 else (0.0, float(values[0]))
        trend_values = intercept + slope * x
        residuals = values - trend_values
        std = float(np.std(residuals)) if n > 1 else float(np.mean(values)) * 0.1

        # Extract weekly seasonality if enough data
        seasonal = np.zeros(seasonal_period)
        if n >= seasonal_period * 2:
            for i in range(n):
                seasonal[i % seasonal_period] += residuals[i]
            counts = np.array([n // seasonal_period + (1 if i < n % seasonal_period else 0) for i in range(seasonal_period)])
            seasonal = seasonal / np.maximum(counts, 1)

        z = self._z_score(confidence)
        last_date = datetime.strptime(data[-1].date, "%Y-%m-%d")
        predictions = []
        for i in range(1, horizon + 1):
            d = last_date + timedelta(days=i)
            pred = intercept + slope * (n + i - 1) + seasonal[(n + i - 1) % seasonal_period]
            predictions.append({
                "date": d.strftime("%Y-%m-%d"),
                "predicted": round(float(pred), 2),
                "lower_bound": round(float(pred - z * std), 2),
                "upper_bound": round(float(pred + z * std), 2),
            })

        return ForecastResult(
            metric=metric,
            method="linear_trend",
            horizon_days=horizon,
            historical=[{"date": p.date, "value": p.value} for p in data[-14:]],
            predictions=predictions,
            model_diagnostics={
                "slope": round(float(slope), 4),
                "intercept": round(float(intercept), 2),
                "residual_std": round(std, 2),
                "has_seasonality": bool(np.any(seasonal != 0)),
            },
            confidence_level=confidence,
        )

    # ------------------------------------------------------------------
    # Fallback
    # ------------------------------------------------------------------

    def _fallback_forecast(
        self,
        metric: str,
        data: list[TimeSeriesPoint],
        horizon: int,
    ) -> ForecastResult:
        """Minimal forecast when insufficient data is available."""
        base = data[-1].value if data else 0.0
        last_date_str = data[-1].date if data else datetime.now(timezone.utc).strftime("%Y-%m-%d")
        last_date = datetime.strptime(last_date_str, "%Y-%m-%d")
        predictions = []
        for i in range(1, horizon + 1):
            d = last_date + timedelta(days=i)
            predictions.append({
                "date": d.strftime("%Y-%m-%d"),
                "predicted": round(base, 2),
                "lower_bound": round(base * 0.8, 2),
                "upper_bound": round(base * 1.2, 2),
            })
        return ForecastResult(
            metric=metric,
            method="fallback_constant",
            horizon_days=horizon,
            historical=[{"date": p.date, "value": p.value} for p in data],
            predictions=predictions,
            model_diagnostics={"note": "Insufficient data; constant forecast used."},
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _z_score(confidence: float) -> float:
        """Return approximate z-score for a given confidence level."""
        table = {0.90: 1.645, 0.95: 1.96, 0.99: 2.576}
        return table.get(confidence, 1.96)
