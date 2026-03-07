"""
Analytics & Reporting Module — Comprehensive Marketing Intelligence

Aggregates data from multiple sources, computes 30+ marketing KPIs
across the AARRR framework, generates visualisations, provides
time-series forecasts, runs multi-touch attribution, detects anomalies,
performs cohort analysis, benchmarks against industry, generates
automated insights, and exports reports.

Engines:
  - KPIEngine: 30+ metrics (Acquisition, Activation, Retention, Revenue, Referral)
  - ForecastingEngine: ARIMA, Holt-Winters, Moving Average, Linear Trend
  - AttributionEngine: First-touch, Last-touch, Linear, Time-decay, Data-driven
  - InsightEngine: LLM-powered + rule-based automated narrative generation
  - AnomalyDetectionEngine: Z-score, IQR, Moving Average, % Change
  - CohortAnalysisEngine: Acquisition, Behavioral, Revenue cohorts
  - BenchmarkingEngine: Industry comparison across 5 verticals
  - ExportEngine: PDF, CSV, JSON, Scheduled email reports
"""

from __future__ import annotations

import math
import random
import uuid
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from .engines.kpi_engine import KPIEngine, RawMetricsInput
from .engines.forecasting_engine import ForecastingEngine, TimeSeriesPoint, ForecastResult
from .engines.attribution_engine import (
    AttributionEngine,
    Touchpoint,
    CustomerJourney,
    AttributionResult,
)
from .engines.insight_engine import InsightEngine, InsightReport
from .engines.anomaly_engine import (
    AnomalyDetectionEngine,
    AnomalyThresholds,
    AnomalyReport,
)
from .engines.cohort_engine import (
    CohortAnalysisEngine,
    CustomerEvent,
    CohortDefinition,
    CohortResult,
)
from .engines.benchmarking_engine import BenchmarkingEngine, BenchmarkReport
from .engines.export_engine import ExportEngine, ExportConfig, EmailSchedule, ExportResult


class AnalyticsReportingModule:
    """
    Provides analytics dashboards, metric computation, forecasting,
    attribution, anomaly detection, cohort analysis, benchmarking,
    automated insights, A/B experiment tracking, and report exports.
    """

    def __init__(self, integrator=None, db=None, memory_manager=None):
        self.integrator = integrator
        self.db = db
        self.memory = memory_manager

        # Initialise engines
        self.kpi_engine = KPIEngine()
        self.forecasting_engine = ForecastingEngine()
        self.attribution_engine = AttributionEngine()
        self.insight_engine = InsightEngine()
        self.anomaly_engine = AnomalyDetectionEngine()
        self.cohort_engine = CohortAnalysisEngine()
        self.benchmarking_engine = BenchmarkingEngine()
        self.export_engine = ExportEngine()

        # In-memory experiment store for MVP
        self._experiments: dict[str, dict] = {}

    # ==================================================================
    # Generic handler (called by Brain orchestrator)
    # ==================================================================

    async def handle(self, message: str, context: dict) -> dict:
        """Generic handler called by the Brain orchestrator."""
        msg = message.lower()

        if "dashboard" in msg or "metric" in msg or "kpi" in msg:
            result = await self.get_dashboard(context=context)
            metrics = result.get("metrics", {})
            summary = "\n".join(
                f"- {k}: {v}" for k, v in metrics.items() if not isinstance(v, dict)
            )
            return {"response": f"Dashboard Metrics (30+ KPIs):\n{summary}"}

        elif "forecast" in msg or "predict" in msg:
            result = await self.get_forecast("revenue", 30)
            fc = result.get("forecast", {})
            return {"response": f"Revenue Forecast ({fc.get('method', 'auto')}): {len(fc.get('predictions', []))} days predicted."}

        elif "attribution" in msg or "channel" in msg:
            result = await self.get_attribution()
            return {"response": f"Attribution analysis complete. Models: {list(result.keys())}"}

        elif "anomal" in msg or "alert" in msg:
            result = await self.detect_anomalies()
            report = result.get("anomaly_report", {})
            return {"response": f"Anomaly scan: {report.get('anomaly_count', 0)} anomalies detected ({report.get('critical_count', 0)} critical)."}

        elif "cohort" in msg or "retention" in msg:
            result = await self.get_cohort_analysis()
            return {"response": f"Cohort analysis complete. {result.get('summary', {}).get('total_cohorts', 0)} cohorts analyzed."}

        elif "benchmark" in msg or "competitor" in msg or "industry" in msg:
            result = await self.get_benchmarks()
            return {"response": f"Benchmark score: {result.get('overall_score', 0)}/100. Strengths: {len(result.get('strengths', []))}, Weaknesses: {len(result.get('weaknesses', []))}"}

        elif "insight" in msg or "recommend" in msg:
            result = await self.get_insights()
            report = result.get("insight_report", {})
            return {"response": f"Insights ({report.get('method', 'rule_based')}): {report.get('executive_summary', 'No insights available.')}"}

        elif "export" in msg or "report" in msg or "pdf" in msg:
            result = await self.export_report(format="pdf")
            return {"response": f"Report exported: {result.get('file_path', 'N/A')}"}

        elif "experiment" in msg or "a/b" in msg:
            return {"response": "Experiment tracking is available. Use /analytics/experiment to record results."}

        else:
            result = await self.get_dashboard(context=context)
            metrics = result.get("metrics", {})
            summary = "\n".join(
                f"- {k}: {v}" for k, v in metrics.items() if not isinstance(v, dict)
            )
            return {"response": f"Analytics Overview (30+ KPIs):\n{summary}"}

    # ==================================================================
    # Dashboard — 30+ KPIs
    # ==================================================================

    async def get_dashboard(
        self,
        params: Optional[dict] = None,
        context: Optional[dict] = None,
        raw_input: Optional[RawMetricsInput] = None,
    ) -> dict:
        """
        Aggregate data and return 30+ KPI metrics and charts.

        Args:
            params: Filter parameters (date_range, channels, campaign_ids).
            context: Additional context (user_id, project_id).
            raw_input: Pre-built RawMetricsInput; if None, sample data is generated.

        Returns:
            Dict with metrics, charts, and metadata.
        """
        params = params or {}
        context = context or {}
        now = datetime.now(timezone.utc)
        days = params.get("days", 30)

        # Use provided raw input or generate sample data
        raw = raw_input or self._generate_sample_raw_input(days)

        # Compute all 30+ KPIs
        metrics = self.kpi_engine.compute_all(raw)

        # Generate chart data
        charts = self._generate_chart_data(days, metrics)

        return {
            "metrics": metrics,
            "charts": charts,
            "metadata": {
                "period_days": days,
                "generated_at": now.isoformat(),
                "data_source": "sample_data" if raw_input is None else "live_data",
                "kpi_count": len([k for k, v in metrics.items() if not isinstance(v, dict)]),
            },
        }

    # ==================================================================
    # Forecasting — Time-Series
    # ==================================================================

    async def get_forecast(
        self,
        metric: str,
        horizon: int = 30,
        params: Optional[dict] = None,
        method: str = "auto",
        historical_data: Optional[list[dict]] = None,
    ) -> dict:
        """
        Generate a time-series forecast for the specified metric.

        Args:
            metric: The metric to forecast (e.g., 'revenue', 'leads', 'spend').
            horizon: Number of days to forecast.
            params: Additional parameters.
            method: Forecasting method ('auto', 'arima', 'holt_winters', etc.).
            historical_data: Optional pre-supplied historical data points.

        Returns:
            Dict with forecast values and confidence intervals.
        """
        # Build historical data
        if historical_data:
            ts_data = [
                TimeSeriesPoint(date=p["date"], value=p["value"])
                for p in historical_data
            ]
        else:
            ts_data = self._generate_sample_time_series(metric, days=90)

        result = self.forecasting_engine.forecast(
            metric_name=metric,
            historical_data=ts_data,
            horizon=horizon,
            method=method,
        )

        return {
            "forecast": {
                "metric": result.metric,
                "horizon_days": result.horizon_days,
                "method": result.method,
                "historical": result.historical,
                "predictions": result.predictions,
                "model_diagnostics": result.model_diagnostics,
                "confidence_level": result.confidence_level,
            },
        }

    # ==================================================================
    # Attribution Modeling
    # ==================================================================

    async def get_attribution(
        self,
        journeys: Optional[list[dict]] = None,
        model: str = "all",
        decay_half_life_days: float = 7.0,
    ) -> dict:
        """
        Run attribution modeling on customer journeys.

        Args:
            journeys: List of journey dicts. If None, sample data is used.
            model: Attribution model or "all" for all five models.
            decay_half_life_days: Half-life for time-decay model.

        Returns:
            Dict with attribution results per model.
        """
        # Parse or generate journeys
        if journeys:
            parsed = self._parse_journeys(journeys)
        else:
            parsed = self._generate_sample_journeys()

        if model == "all":
            results = self.attribution_engine.attribute_all_models(
                parsed, decay_half_life_days
            )
            return {
                m: {
                    "model": r.model,
                    "channel_scores": r.channel_scores,
                    "channel_conversions": r.channel_conversions,
                    "channel_cost": r.channel_cost,
                    "channel_roas": r.channel_roas,
                    "total_conversions": r.total_conversions,
                    "total_value": r.total_value,
                }
                for m, r in results.items()
            }
        else:
            result = self.attribution_engine.attribute(
                parsed, model=model, decay_half_life_days=decay_half_life_days
            )
            return {
                result.model: {
                    "model": result.model,
                    "channel_scores": result.channel_scores,
                    "channel_conversions": result.channel_conversions,
                    "channel_cost": result.channel_cost,
                    "channel_roas": result.channel_roas,
                    "total_conversions": result.total_conversions,
                    "total_value": result.total_value,
                }
            }

    # ==================================================================
    # Automated Insights
    # ==================================================================

    async def get_insights(
        self,
        metrics: Optional[dict] = None,
        period_description: str = "last 30 days",
        use_llm: bool = True,
    ) -> dict:
        """
        Generate automated insights from metrics.

        Args:
            metrics: KPI dict. If None, dashboard metrics are computed.
            period_description: Human-readable period.
            use_llm: Whether to use LLM for enhanced insights.

        Returns:
            Dict with executive summary and insight list.
        """
        if metrics is None:
            dashboard = await self.get_dashboard()
            metrics = dashboard.get("metrics", {})

        report = await self.insight_engine.generate_insights(
            metrics, period_description, use_llm
        )

        return {
            "insight_report": {
                "executive_summary": report.executive_summary,
                "insights": [
                    {
                        "category": i.category,
                        "severity": i.severity,
                        "title": i.title,
                        "narrative": i.narrative,
                        "suggested_actions": i.suggested_actions,
                        "related_metrics": i.related_metrics,
                        "confidence": i.confidence,
                    }
                    for i in report.insights
                ],
                "generated_at": report.generated_at,
                "method": report.method,
            }
        }

    # ==================================================================
    # Anomaly Detection
    # ==================================================================

    async def detect_anomalies(
        self,
        current_metrics: Optional[dict] = None,
        historical_metrics: Optional[list[dict]] = None,
    ) -> dict:
        """
        Detect anomalies in current metrics vs. historical data.

        Returns:
            Dict with anomaly report.
        """
        if current_metrics is None:
            dashboard = await self.get_dashboard()
            current_metrics = dashboard.get("metrics", {})

        if historical_metrics is None:
            historical_metrics = self._generate_sample_historical_metrics(periods=12)

        report = self.anomaly_engine.detect_anomalies(
            current_metrics={
                k: v for k, v in current_metrics.items() if isinstance(v, (int, float))
            },
            historical_metrics=historical_metrics,
        )

        return {
            "anomaly_report": {
                "anomalies": [
                    {
                        "metric": a.metric,
                        "current_value": a.current_value,
                        "expected_value": a.expected_value,
                        "deviation": a.deviation,
                        "severity": a.severity,
                        "method": a.method,
                        "direction": a.direction,
                        "message": a.message,
                    }
                    for a in report.anomalies
                ],
                "total_metrics_checked": report.total_metrics_checked,
                "anomaly_count": report.anomaly_count,
                "critical_count": report.critical_count,
                "warning_count": report.warning_count,
                "generated_at": report.generated_at,
            }
        }

    # ==================================================================
    # Cohort Analysis
    # ==================================================================

    async def get_cohort_analysis(
        self,
        events: Optional[list[dict]] = None,
        cohort_type: str = "acquisition",
        period: str = "month",
        retention_event: str = "purchase",
        num_periods: int = 12,
    ) -> dict:
        """
        Perform cohort analysis on customer events.

        Returns:
            Dict with retention matrix and cohort metrics.
        """
        if events:
            parsed_events = [
                CustomerEvent(
                    customer_id=e["customer_id"],
                    event_type=e.get("event_type", "purchase"),
                    timestamp=e["timestamp"],
                    revenue=e.get("revenue", 0.0),
                    properties=e.get("properties", {}),
                )
                for e in events
            ]
        else:
            parsed_events = self._generate_sample_cohort_events()

        defn = CohortDefinition(
            cohort_type=cohort_type,
            period=period,
            retention_event=retention_event,
            num_periods=num_periods,
        )

        result = self.cohort_engine.analyze(parsed_events, defn)

        return {
            "cohort_type": result.cohort_type,
            "period": result.period,
            "cohort_labels": result.cohort_labels,
            "retention_matrix": result.retention_matrix,
            "cohort_sizes": result.cohort_sizes,
            "avg_retention_by_period": result.avg_retention_by_period,
            "ltv_by_cohort": result.ltv_by_cohort,
            "revenue_matrix": result.revenue_matrix,
            "summary": result.summary,
        }

    # ==================================================================
    # Competitive Benchmarking
    # ==================================================================

    async def get_benchmarks(
        self,
        metrics: Optional[dict] = None,
        industry: str = "saas",
    ) -> dict:
        """
        Compare metrics against industry benchmarks.

        Returns:
            Dict with benchmark comparisons and overall score.
        """
        if metrics is None:
            dashboard = await self.get_dashboard()
            metrics = dashboard.get("metrics", {})

        report = self.benchmarking_engine.compare(
            your_metrics={
                k: v for k, v in metrics.items() if isinstance(v, (int, float))
            },
            industry=industry,
        )

        return {
            "industry": report.industry,
            "overall_score": report.overall_score,
            "comparisons": [
                {
                    "metric": c.metric,
                    "your_value": c.your_value,
                    "industry_avg": c.industry_avg,
                    "industry_p25": c.industry_p25,
                    "industry_p75": c.industry_p75,
                    "best_in_class": c.best_in_class,
                    "percentile_rank": c.percentile_rank,
                    "gap_to_avg": c.gap_to_avg,
                    "gap_to_best": c.gap_to_best,
                    "assessment": c.assessment,
                }
                for c in report.comparisons
            ],
            "strengths": report.strengths,
            "weaknesses": report.weaknesses,
            "generated_at": report.generated_at,
        }

    # ==================================================================
    # A/B Experiment Tracking
    # ==================================================================

    async def record_experiment(
        self,
        experiment_id: str,
        variants: list[dict],
        results: Optional[dict] = None,
    ) -> dict:
        """
        Store A/B test results and calculate uplift and significance.

        Args:
            experiment_id: Unique experiment identifier.
            variants: List of variant dicts with name, sample_size, conversions.
            results: Optional pre-computed results.

        Returns:
            Dict with experiment statistics and recommendations.
        """
        if not variants or len(variants) < 2:
            return {
                "experiment_results": {
                    "error": "At least 2 variants are required for an experiment."
                }
            }

        control = variants[0]
        control_rate = (
            control.get("conversions", 0) / max(control.get("sample_size", 1), 1)
        )

        variant_results = []
        for v in variants:
            rate = v.get("conversions", 0) / max(v.get("sample_size", 1), 1)
            uplift = ((rate - control_rate) / max(control_rate, 0.001)) * 100

            n1 = max(control.get("sample_size", 1), 1)
            n2 = max(v.get("sample_size", 1), 1)
            p_pooled = (
                (control.get("conversions", 0) + v.get("conversions", 0)) / (n1 + n2)
            )
            se = math.sqrt(max(p_pooled * (1 - p_pooled) * (1 / n1 + 1 / n2), 1e-10))
            z_score = (rate - control_rate) / max(se, 1e-10)
            p_value = self._z_to_p(z_score)
            is_significant = abs(z_score) > 1.96

            # Statistical power estimation
            power = self._estimate_power(n1, n2, control_rate, rate)

            variant_results.append({
                "name": v.get("name", "Unknown"),
                "sample_size": v.get("sample_size", 0),
                "conversions": v.get("conversions", 0),
                "conversion_rate": round(rate * 100, 2),
                "uplift_percent": round(uplift, 2),
                "z_score": round(z_score, 4),
                "p_value": round(p_value, 4),
                "is_significant": is_significant,
                "statistical_power": round(power, 2),
                "confidence_interval": {
                    "lower": round((rate - 1.96 * se) * 100, 2),
                    "upper": round((rate + 1.96 * se) * 100, 2),
                },
            })

        best = max(variant_results, key=lambda x: x["conversion_rate"])
        recommendation = (
            f"Variant '{best['name']}' has the highest conversion rate "
            f"({best['conversion_rate']}%)."
        )
        if best["is_significant"]:
            recommendation += " The result is statistically significant at 95% confidence."
        else:
            recommendation += " However, the result is not yet statistically significant. Consider collecting more data."

        experiment = {
            "id": experiment_id,
            "variants": variant_results,
            "recommendation": recommendation,
            "status": "completed",
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
        }
        self._experiments[experiment_id] = experiment

        return {"experiment_results": experiment}

    # ==================================================================
    # Export Reports
    # ==================================================================

    async def export_report(
        self,
        format: str = "pdf",
        include_all: bool = True,
        data: Optional[dict] = None,
        config: Optional[dict] = None,
    ) -> dict:
        """
        Export a comprehensive analytics report.

        Args:
            format: Export format ('pdf', 'csv', 'json').
            include_all: Whether to include all analytics sections.
            data: Pre-built data dict. If None, all sections are computed.
            config: Export configuration overrides.

        Returns:
            Dict with export result.
        """
        if data is None:
            data = {}
            dashboard = await self.get_dashboard()
            data["metrics"] = dashboard.get("metrics", {})

            if include_all:
                # Forecasts
                forecast = await self.get_forecast("revenue", 30)
                data["forecast"] = forecast.get("forecast", {})

                # Insights
                insights = await self.get_insights(
                    metrics=data["metrics"], use_llm=False
                )
                report = insights.get("insight_report", {})
                data["executive_summary"] = report.get("executive_summary", "")
                data["insights"] = report.get("insights", [])

                # Anomalies
                anomalies = await self.detect_anomalies(
                    current_metrics=data["metrics"]
                )
                data["anomalies"] = anomalies.get("anomaly_report", {}).get("anomalies", [])

                # Benchmarks
                benchmarks = await self.get_benchmarks(metrics=data["metrics"])
                data["benchmarks"] = benchmarks

        export_config = ExportConfig(
            format=format,
            **(config or {}),
        )

        result = self.export_engine.export(data, export_config)

        return {
            "success": result.success,
            "format": result.format,
            "file_path": result.file_path,
            "file_size_bytes": result.file_size_bytes,
            "error": result.error,
            "generated_at": result.generated_at,
        }

    # ==================================================================
    # KPI Catalog
    # ==================================================================

    def get_kpi_catalog(self) -> list[dict]:
        """Return the full catalog of 30+ KPIs with metadata."""
        return self.kpi_engine.get_catalog()

    def get_supported_industries(self) -> list[str]:
        """Return list of industries with available benchmarks."""
        return self.benchmarking_engine.get_supported_industries()

    # ==================================================================
    # Private helpers
    # ==================================================================

    def _generate_chart_data(self, days: int, metrics: dict) -> list[dict]:
        """Generate chart data in Plotly-compatible format."""
        now = datetime.now(timezone.utc)
        dates = [
            (now - timedelta(days=days - i)).strftime("%Y-%m-%d") for i in range(days)
        ]

        spend_chart = {
            "id": "spend_over_time",
            "type": "line",
            "title": "Marketing Spend Over Time",
            "data": {
                "x": dates,
                "y": [round(random.uniform(100, 800), 2) for _ in dates],
            },
            "layout": {"xaxis_title": "Date", "yaxis_title": "Spend ($)"},
        }

        channels = ["Email", "Social", "Paid Search", "Display", "Organic"]
        channel_chart = {
            "id": "conversions_by_channel",
            "type": "bar",
            "title": "Conversions by Channel",
            "data": {
                "x": channels,
                "y": [random.randint(5, 50) for _ in channels],
            },
            "layout": {"xaxis_title": "Channel", "yaxis_title": "Conversions"},
        }

        funnel_chart = {
            "id": "conversion_funnel",
            "type": "funnel",
            "title": "Conversion Funnel",
            "data": {
                "labels": ["Impressions", "Clicks", "Leads", "MQLs", "SQLs", "Customers"],
                "values": [
                    metrics.get("impressions", 100000),
                    metrics.get("clicks", 5000),
                    metrics.get("sessions", 500) if "sessions" in metrics else 500,
                    100,
                    40,
                    metrics.get("conversions", 25) if isinstance(metrics.get("conversions"), int) else 25,
                ],
            },
        }

        # AARRR stage breakdown chart
        aarrr_chart = {
            "id": "aarrr_funnel",
            "type": "bar",
            "title": "AARRR Framework Performance",
            "data": {
                "x": ["Acquisition", "Activation", "Retention", "Revenue", "Referral"],
                "y": [
                    metrics.get("ctr", 0),
                    metrics.get("activation_rate", 0),
                    metrics.get("retention_rate", 0),
                    metrics.get("roas", 0) * 10,  # Scale for visibility
                    metrics.get("viral_coefficient", 0) * 100,
                ],
            },
            "layout": {"xaxis_title": "Stage", "yaxis_title": "Score"},
        }

        # Revenue trend
        revenue_chart = {
            "id": "revenue_trend",
            "type": "line",
            "title": "Revenue Trend",
            "data": {
                "x": dates,
                "y": [round(random.uniform(500, 2000), 2) for _ in dates],
            },
            "layout": {"xaxis_title": "Date", "yaxis_title": "Revenue ($)"},
        }

        return [spend_chart, channel_chart, funnel_chart, aarrr_chart, revenue_chart]

    @staticmethod
    def _generate_sample_raw_input(days: int = 30) -> RawMetricsInput:
        """Generate realistic sample raw metrics for demo/testing."""
        return RawMetricsInput(
            impressions=random.randint(80000, 200000),
            clicks=random.randint(2000, 10000),
            sessions=random.randint(3000, 15000),
            unique_visitors=random.randint(2000, 12000),
            new_visitors=random.randint(1000, 8000),
            returning_visitors=random.randint(500, 4000),
            organic_sessions=random.randint(500, 3000),
            paid_sessions=random.randint(500, 3000),
            social_sessions=random.randint(200, 1500),
            referral_sessions=random.randint(100, 800),
            direct_sessions=random.randint(300, 2000),
            total_ad_spend=round(random.uniform(5000, 25000), 2),
            total_marketing_spend=round(random.uniform(8000, 40000), 2),
            total_leads=random.randint(200, 800),
            new_leads=random.randint(50, 200),
            marketing_qualified_leads=random.randint(30, 150),
            sales_qualified_leads=random.randint(10, 60),
            signups=random.randint(100, 500),
            activations=random.randint(40, 200),
            trial_starts=random.randint(20, 100),
            onboarding_completions=random.randint(30, 150),
            conversions=random.randint(20, 100),
            purchases=random.randint(15, 80),
            demo_requests=random.randint(5, 40),
            total_revenue=round(random.uniform(20000, 100000), 2),
            new_revenue=round(random.uniform(5000, 30000), 2),
            expansion_revenue=round(random.uniform(2000, 10000), 2),
            churned_revenue=round(random.uniform(1000, 5000), 2),
            total_customers=random.randint(200, 1000),
            new_customers=random.randint(20, 100),
            churned_customers=random.randint(5, 30),
            active_users_start=random.randint(500, 2000),
            active_users_end=random.randint(500, 2000),
            returning_customers=random.randint(100, 500),
            support_tickets=random.randint(10, 100),
            nps_responses=[random.randint(0, 10) for _ in range(50)],
            emails_sent=random.randint(5000, 20000),
            emails_delivered=random.randint(4500, 19000),
            emails_opened=random.randint(1000, 6000),
            emails_clicked=random.randint(200, 1500),
            emails_bounced=random.randint(50, 500),
            emails_unsubscribed=random.randint(10, 100),
            referral_invites_sent=random.randint(50, 300),
            referral_invites_accepted=random.randint(20, 150),
            referral_conversions=random.randint(5, 50),
            page_views=random.randint(10000, 50000),
            avg_session_duration_seconds=round(random.uniform(60, 300), 1),
            bounce_rate_raw=round(random.uniform(30, 65), 1),
            pages_per_session=round(random.uniform(1.5, 5.0), 2),
            avg_customer_lifespan_months=round(random.uniform(8, 24), 1),
            avg_revenue_per_customer_monthly=round(random.uniform(50, 200), 2),
            period_days=days,
        )

    @staticmethod
    def _generate_sample_time_series(metric: str, days: int = 90) -> list[TimeSeriesPoint]:
        """Generate sample historical time-series data."""
        now = datetime.now(timezone.utc)
        base = {"revenue": 1000, "leads": 15, "spend": 500, "sessions": 200}.get(metric, 100)
        points = []
        value = base
        for i in range(days):
            date = now - timedelta(days=days - i)
            # Add trend + seasonality + noise
            trend = base * 0.002 * i
            seasonal = base * 0.1 * math.sin(2 * math.pi * i / 7)
            noise = random.gauss(0, base * 0.05)
            value = base + trend + seasonal + noise
            points.append(TimeSeriesPoint(
                date=date.strftime("%Y-%m-%d"),
                value=round(max(value, 0), 2),
            ))
        return points

    @staticmethod
    def _generate_sample_journeys(n: int = 200) -> list[CustomerJourney]:
        """Generate sample customer journeys for attribution."""
        channels = ["Organic Search", "Paid Search", "Social Media", "Email", "Display", "Referral"]
        now = datetime.now(timezone.utc)
        journeys = []

        for i in range(n):
            num_touches = random.randint(1, 6)
            touchpoints = []
            for j in range(num_touches):
                ts = now - timedelta(days=random.randint(1, 60), hours=random.randint(0, 23))
                touchpoints.append(Touchpoint(
                    channel=random.choice(channels),
                    timestamp=ts.strftime("%Y-%m-%dT%H:%M:%S"),
                    campaign_id=f"camp-{random.randint(1, 10):03d}",
                    cost=round(random.uniform(0.5, 10.0), 2),
                ))
            touchpoints.sort(key=lambda t: t.timestamp)

            converted = random.random() < 0.3
            journeys.append(CustomerJourney(
                customer_id=f"cust-{i:04d}",
                touchpoints=touchpoints,
                converted=converted,
                conversion_value=round(random.uniform(50, 500), 2) if converted else 0.0,
            ))

        return journeys

    @staticmethod
    def _generate_sample_cohort_events(
        num_customers: int = 300,
        months: int = 6,
    ) -> list[CustomerEvent]:
        """Generate sample customer events for cohort analysis."""
        events = []
        now = datetime.now(timezone.utc)

        for i in range(num_customers):
            cid = f"cust-{i:04d}"
            signup_month = random.randint(0, months - 1)
            signup_date = now - timedelta(days=signup_month * 30 + random.randint(0, 29))

            events.append(CustomerEvent(
                customer_id=cid,
                event_type="signup",
                timestamp=signup_date.strftime("%Y-%m-%dT%H:%M:%S"),
                revenue=0.0,
            ))

            # Simulate purchases over time with decreasing probability
            for m in range(signup_month + 1):
                if random.random() < (0.6 * (0.85 ** m)):
                    purchase_date = signup_date + timedelta(days=m * 30 + random.randint(1, 28))
                    if purchase_date <= now:
                        events.append(CustomerEvent(
                            customer_id=cid,
                            event_type="purchase",
                            timestamp=purchase_date.strftime("%Y-%m-%dT%H:%M:%S"),
                            revenue=round(random.uniform(20, 200), 2),
                        ))

        return events

    @staticmethod
    def _generate_sample_historical_metrics(periods: int = 12) -> list[dict]:
        """Generate historical metric snapshots for anomaly detection."""
        history = []
        for _ in range(periods):
            history.append({
                "ctr": round(random.uniform(1.5, 4.0), 2),
                "conversion_rate": round(random.uniform(1.5, 5.0), 2),
                "cac": round(random.uniform(80, 180), 2),
                "roas": round(random.uniform(2.5, 6.0), 2),
                "churn_rate": round(random.uniform(2.0, 6.0), 2),
                "email_open_rate": round(random.uniform(18, 30), 1),
                "bounce_rate": round(random.uniform(35, 55), 1),
                "ltv_cac_ratio": round(random.uniform(2.0, 5.0), 2),
            })
        return history

    @staticmethod
    def _parse_journeys(raw_journeys: list[dict]) -> list[CustomerJourney]:
        """Parse raw journey dicts into CustomerJourney objects."""
        journeys = []
        for j in raw_journeys:
            touchpoints = [
                Touchpoint(
                    channel=tp.get("channel", "unknown"),
                    timestamp=tp.get("timestamp", ""),
                    campaign_id=tp.get("campaign_id"),
                    cost=tp.get("cost", 0.0),
                )
                for tp in j.get("touchpoints", [])
            ]
            journeys.append(CustomerJourney(
                customer_id=j.get("customer_id", str(uuid.uuid4())),
                touchpoints=touchpoints,
                converted=j.get("converted", False),
                conversion_value=j.get("conversion_value", 0.0),
            ))
        return journeys

    @staticmethod
    def _z_to_p(z: float) -> float:
        """Approximate two-tailed p-value from z-score."""
        # Using the complementary error function approximation
        return 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))

    @staticmethod
    def _estimate_power(n1: int, n2: int, p1: float, p2: float) -> float:
        """Estimate statistical power of the test."""
        if p1 == p2:
            return 0.05  # No effect
        effect_size = abs(p2 - p1) / max(
            math.sqrt((p1 * (1 - p1) + p2 * (1 - p2)) / 2), 1e-10
        )
        n_harmonic = 2 * n1 * n2 / max(n1 + n2, 1)
        ncp = effect_size * math.sqrt(n_harmonic)
        # Approximate power
        power = min(0.99, 0.5 * (1 + math.erf((ncp - 1.96) / math.sqrt(2))))
        return max(power, 0.05)
