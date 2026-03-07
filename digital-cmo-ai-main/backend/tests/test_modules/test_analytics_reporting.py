"""
Comprehensive Unit Tests for the Analytics & Reporting Module.

Tests cover all 8 engines and the main module orchestrator:
  - KPI Engine (30+ metrics, AARRR framework)
  - Forecasting Engine (ARIMA, Holt-Winters, Moving Average, Linear Trend)
  - Attribution Engine (5 models)
  - Insight Engine (rule-based)
  - Anomaly Detection Engine (Z-score, IQR, MA, % change)
  - Cohort Analysis Engine (acquisition, behavioral, revenue)
  - Benchmarking Engine (industry comparison)
  - Export Engine (PDF, CSV, JSON)
  - Main Module (orchestrator integration)
"""

import math
import os
import json
import tempfile
from datetime import datetime, timedelta, timezone

import pytest
import numpy as np

from app.modules.analytics_reporting import AnalyticsReportingModule
from app.modules.analytics_reporting.engines.kpi_engine import (
    KPIEngine,
    RawMetricsInput,
    KPI_CATALOG,
)
from app.modules.analytics_reporting.engines.forecasting_engine import (
    ForecastingEngine,
    TimeSeriesPoint,
)
from app.modules.analytics_reporting.engines.attribution_engine import (
    AttributionEngine,
    Touchpoint,
    CustomerJourney,
)
from app.modules.analytics_reporting.engines.insight_engine import InsightEngine
from app.modules.analytics_reporting.engines.anomaly_engine import (
    AnomalyDetectionEngine,
    AnomalyThresholds,
)
from app.modules.analytics_reporting.engines.cohort_engine import (
    CohortAnalysisEngine,
    CustomerEvent,
    CohortDefinition,
)
from app.modules.analytics_reporting.engines.benchmarking_engine import BenchmarkingEngine
from app.modules.analytics_reporting.engines.export_engine import (
    ExportEngine,
    ExportConfig,
)


# ==================================================================
# Fixtures
# ==================================================================

@pytest.fixture
def module():
    return AnalyticsReportingModule()


@pytest.fixture
def kpi_engine():
    return KPIEngine()


@pytest.fixture
def forecasting_engine():
    return ForecastingEngine()


@pytest.fixture
def attribution_engine():
    return AttributionEngine()


@pytest.fixture
def insight_engine():
    return InsightEngine()


@pytest.fixture
def anomaly_engine():
    return AnomalyDetectionEngine()


@pytest.fixture
def cohort_engine():
    return CohortAnalysisEngine()


@pytest.fixture
def benchmarking_engine():
    return BenchmarkingEngine()


@pytest.fixture
def export_engine():
    return ExportEngine()


@pytest.fixture
def sample_raw_input():
    return RawMetricsInput(
        impressions=100000,
        clicks=3000,
        sessions=5000,
        unique_visitors=4000,
        new_visitors=2500,
        returning_visitors=1500,
        organic_sessions=1500,
        paid_sessions=1200,
        social_sessions=800,
        referral_sessions=300,
        direct_sessions=1200,
        total_ad_spend=10000.0,
        total_marketing_spend=15000.0,
        total_leads=300,
        new_leads=100,
        marketing_qualified_leads=60,
        sales_qualified_leads=25,
        signups=200,
        activations=80,
        trial_starts=50,
        onboarding_completions=70,
        conversions=40,
        purchases=35,
        demo_requests=15,
        total_revenue=50000.0,
        new_revenue=15000.0,
        expansion_revenue=5000.0,
        churned_revenue=2000.0,
        total_customers=500,
        new_customers=50,
        churned_customers=15,
        active_users_start=800,
        active_users_end=850,
        returning_customers=200,
        support_tickets=30,
        nps_responses=[9, 10, 8, 7, 9, 10, 6, 5, 9, 10, 8, 9, 3, 10, 9],
        emails_sent=10000,
        emails_delivered=9500,
        emails_opened=2500,
        emails_clicked=500,
        emails_bounced=200,
        emails_unsubscribed=30,
        referral_invites_sent=100,
        referral_invites_accepted=40,
        referral_conversions=15,
        page_views=25000,
        avg_session_duration_seconds=180.5,
        bounce_rate_raw=42.3,
        pages_per_session=3.2,
        avg_customer_lifespan_months=14.0,
        avg_revenue_per_customer_monthly=120.0,
        period_days=30,
    )


@pytest.fixture
def sample_time_series():
    now = datetime.now(timezone.utc)
    return [
        TimeSeriesPoint(
            date=(now - timedelta(days=90 - i)).strftime("%Y-%m-%d"),
            value=round(1000 + 5 * i + 50 * math.sin(2 * math.pi * i / 7) + np.random.normal(0, 20), 2),
        )
        for i in range(90)
    ]


@pytest.fixture
def sample_journeys():
    now = datetime.now(timezone.utc)
    channels = ["Organic", "Paid Search", "Social", "Email", "Display"]
    journeys = []
    for i in range(50):
        tps = []
        for j in range(3):
            ts = now - timedelta(days=30 - j * 10, hours=i % 24)
            tps.append(Touchpoint(
                channel=channels[j % len(channels)],
                timestamp=ts.strftime("%Y-%m-%dT%H:%M:%S"),
                cost=5.0,
            ))
        converted = i % 3 == 0
        journeys.append(CustomerJourney(
            customer_id=f"cust-{i:03d}",
            touchpoints=tps,
            converted=converted,
            conversion_value=100.0 if converted else 0.0,
        ))
    return journeys


@pytest.fixture
def sample_cohort_events():
    now = datetime.now(timezone.utc)
    events = []
    for i in range(100):
        cid = f"cust-{i:03d}"
        signup = now - timedelta(days=180 - (i % 6) * 30)
        events.append(CustomerEvent(
            customer_id=cid,
            event_type="signup",
            timestamp=signup.strftime("%Y-%m-%dT%H:%M:%S"),
        ))
        # Simulate purchases
        for m in range(3):
            if (i + m) % 2 == 0:
                purchase_date = signup + timedelta(days=m * 30 + 5)
                if purchase_date <= now:
                    events.append(CustomerEvent(
                        customer_id=cid,
                        event_type="purchase",
                        timestamp=purchase_date.strftime("%Y-%m-%dT%H:%M:%S"),
                        revenue=50.0 + i * 0.5,
                    ))
    return events


# ==================================================================
# KPI Engine Tests
# ==================================================================

class TestKPIEngine:
    """Tests for the 30+ KPI computation engine."""

    def test_compute_all_returns_30_plus_metrics(self, kpi_engine, sample_raw_input):
        result = kpi_engine.compute_all(sample_raw_input)
        # Count non-dict metrics
        scalar_metrics = {k: v for k, v in result.items() if not isinstance(v, dict)}
        assert len(scalar_metrics) >= 30, f"Expected 30+ metrics, got {len(scalar_metrics)}"

    def test_acquisition_metrics(self, kpi_engine, sample_raw_input):
        result = kpi_engine.compute_all(sample_raw_input)
        assert result["impressions"] == 100000
        assert result["clicks"] == 3000
        assert result["ctr"] == 3.0  # 3000/100000 * 100
        assert result["cpc"] == round(10000 / 3000, 2)
        assert result["cpm"] == round(10000 * 1000 / 100000, 2)

    def test_activation_metrics(self, kpi_engine, sample_raw_input):
        result = kpi_engine.compute_all(sample_raw_input)
        assert result["signup_rate"] == round(200 / 5000 * 100, 2)
        assert result["activation_rate"] == round(80 / 200 * 100, 2)

    def test_retention_metrics(self, kpi_engine, sample_raw_input):
        result = kpi_engine.compute_all(sample_raw_input)
        assert result["retention_rate"] == round((500 - 15) / 500 * 100, 2)
        assert result["churn_rate"] == round(15 / 500 * 100, 2)

    def test_revenue_metrics(self, kpi_engine, sample_raw_input):
        result = kpi_engine.compute_all(sample_raw_input)
        assert result["total_revenue"] == 50000.0
        assert result["roas"] == round(50000 / 10000, 2)
        assert result["ltv"] == round(120 * 14, 2)
        assert result["arpu"] == round(50000 / 500, 2)

    def test_referral_metrics(self, kpi_engine, sample_raw_input):
        result = kpi_engine.compute_all(sample_raw_input)
        assert result["referral_rate"] == round(100 / 500 * 100, 2)
        assert result["referral_conversion_rate"] == round(15 / 40 * 100, 2)

    def test_email_metrics(self, kpi_engine, sample_raw_input):
        result = kpi_engine.compute_all(sample_raw_input)
        assert result["email_open_rate"] == round(2500 / 9500 * 100, 2)
        assert result["email_click_rate"] == round(500 / 9500 * 100, 2)

    def test_nps_calculation(self, kpi_engine, sample_raw_input):
        result = kpi_engine.compute_all(sample_raw_input)
        nps = result["net_promoter_score"]
        assert -100 <= nps <= 100

    def test_compute_stage_filters_correctly(self, kpi_engine, sample_raw_input):
        acq = kpi_engine.compute_stage(sample_raw_input, "acquisition")
        assert "ctr" in acq
        assert "churn_rate" not in acq

    def test_kpi_catalog_has_30_plus_entries(self, kpi_engine):
        catalog = kpi_engine.get_catalog()
        assert len(catalog) >= 30

    def test_zero_denominator_safety(self, kpi_engine):
        raw = RawMetricsInput()  # All zeros
        result = kpi_engine.compute_all(raw)
        assert result["ctr"] == 0.0
        assert result["cac"] == 0.0
        assert result["roas"] == 0.0

    def test_traffic_channel_mix(self, kpi_engine, sample_raw_input):
        result = kpi_engine.compute_all(sample_raw_input)
        mix = result["traffic_channel_mix"]
        assert isinstance(mix, dict)
        assert "organic" in mix
        assert mix["organic"] == 1500


# ==================================================================
# Forecasting Engine Tests
# ==================================================================

class TestForecastingEngine:
    """Tests for the time-series forecasting engine."""

    def test_linear_trend_forecast(self, forecasting_engine, sample_time_series):
        result = forecasting_engine.forecast(
            "revenue", sample_time_series, horizon=14, method="linear_trend"
        )
        assert result.metric == "revenue"
        assert result.method == "linear_trend"
        assert len(result.predictions) == 14
        assert all("predicted" in p for p in result.predictions)
        assert all("lower_bound" in p for p in result.predictions)
        assert all("upper_bound" in p for p in result.predictions)

    def test_moving_average_forecast(self, forecasting_engine, sample_time_series):
        result = forecasting_engine.forecast(
            "leads", sample_time_series, horizon=7, method="moving_average"
        )
        assert result.method == "moving_average"
        assert len(result.predictions) == 7

    def test_holt_winters_forecast(self, forecasting_engine, sample_time_series):
        result = forecasting_engine.forecast(
            "revenue", sample_time_series, horizon=14, method="holt_winters"
        )
        assert len(result.predictions) == 14
        # Should use holt_winters or fallback
        assert result.method in ("holt_winters", "linear_trend")

    def test_arima_forecast(self, forecasting_engine, sample_time_series):
        result = forecasting_engine.forecast(
            "revenue", sample_time_series, horizon=14, method="arima"
        )
        assert len(result.predictions) == 14
        assert result.method in ("arima", "linear_trend")

    def test_auto_method_selection(self, forecasting_engine, sample_time_series):
        result = forecasting_engine.forecast(
            "revenue", sample_time_series, horizon=14, method="auto"
        )
        assert result.method in ForecastingEngine.SUPPORTED_METHODS

    def test_fallback_on_insufficient_data(self, forecasting_engine):
        short_data = [TimeSeriesPoint(date="2025-01-01", value=100)]
        result = forecasting_engine.forecast("test", short_data, horizon=5)
        assert result.method == "fallback_constant"
        assert len(result.predictions) == 5

    def test_forecast_confidence_intervals(self, forecasting_engine, sample_time_series):
        result = forecasting_engine.forecast(
            "revenue", sample_time_series, horizon=7, method="linear_trend"
        )
        for p in result.predictions:
            assert p["lower_bound"] <= p["predicted"] <= p["upper_bound"]

    def test_forecast_diagnostics(self, forecasting_engine, sample_time_series):
        result = forecasting_engine.forecast(
            "revenue", sample_time_series, horizon=7, method="linear_trend"
        )
        assert "slope" in result.model_diagnostics
        assert "intercept" in result.model_diagnostics


# ==================================================================
# Attribution Engine Tests
# ==================================================================

class TestAttributionEngine:
    """Tests for the multi-touch attribution engine."""

    def test_first_touch_attribution(self, attribution_engine, sample_journeys):
        result = attribution_engine.attribute(sample_journeys, model="first_touch")
        assert result.model == "first_touch"
        assert sum(result.channel_scores.values()) > 0
        assert result.total_conversions > 0

    def test_last_touch_attribution(self, attribution_engine, sample_journeys):
        result = attribution_engine.attribute(sample_journeys, model="last_touch")
        assert result.model == "last_touch"
        assert sum(result.channel_scores.values()) > 0

    def test_linear_attribution(self, attribution_engine, sample_journeys):
        result = attribution_engine.attribute(sample_journeys, model="linear")
        assert result.model == "linear"
        total_attributed = sum(result.channel_scores.values())
        assert total_attributed > 0

    def test_time_decay_attribution(self, attribution_engine, sample_journeys):
        result = attribution_engine.attribute(
            sample_journeys, model="time_decay", decay_half_life_days=7.0
        )
        assert result.model == "time_decay"
        assert sum(result.channel_scores.values()) > 0

    def test_data_driven_attribution(self, attribution_engine, sample_journeys):
        result = attribution_engine.attribute(sample_journeys, model="data_driven")
        assert result.model == "data_driven"
        # Data-driven should distribute across channels
        assert len(result.channel_scores) > 0

    def test_all_models(self, attribution_engine, sample_journeys):
        results = attribution_engine.attribute_all_models(sample_journeys)
        assert len(results) == 5
        for model_name in AttributionEngine.SUPPORTED_MODELS:
            assert model_name in results

    def test_attribution_roas(self, attribution_engine, sample_journeys):
        result = attribution_engine.attribute(sample_journeys, model="linear")
        for ch, roas in result.channel_roas.items():
            assert isinstance(roas, float)

    def test_empty_journeys(self, attribution_engine):
        result = attribution_engine.attribute([], model="linear")
        assert result.total_conversions == 0

    def test_single_touchpoint_journey(self, attribution_engine):
        journeys = [
            CustomerJourney(
                customer_id="c1",
                touchpoints=[Touchpoint(channel="Email", timestamp="2025-01-01T10:00:00", cost=5.0)],
                converted=True,
                conversion_value=100.0,
            )
        ]
        result = attribution_engine.attribute(journeys, model="linear")
        assert result.channel_scores.get("Email", 0) == 100.0


# ==================================================================
# Insight Engine Tests
# ==================================================================

class TestInsightEngine:
    """Tests for the automated insight generation engine."""

    @pytest.mark.asyncio
    async def test_rule_based_insights_low_ctr(self, insight_engine):
        metrics = {"ctr": 0.5, "impressions": 100000, "clicks": 500}
        report = await insight_engine.generate_insights(metrics, use_llm=False)
        assert report.method == "rule_based"
        assert any("CTR" in i.title or "Click" in i.title for i in report.insights)

    @pytest.mark.asyncio
    async def test_rule_based_insights_high_roas(self, insight_engine):
        metrics = {"roas": 8.0, "total_revenue": 80000, "total_ad_spend": 10000}
        report = await insight_engine.generate_insights(metrics, use_llm=False)
        positives = [i for i in report.insights if i.severity == "positive"]
        assert len(positives) > 0

    @pytest.mark.asyncio
    async def test_rule_based_insights_high_churn(self, insight_engine):
        metrics = {"churn_rate": 8.0, "retention_rate": 92.0}
        report = await insight_engine.generate_insights(metrics, use_llm=False)
        warnings = [i for i in report.insights if i.severity in ("warning", "critical")]
        assert len(warnings) > 0

    @pytest.mark.asyncio
    async def test_executive_summary_generated(self, insight_engine):
        metrics = {"ctr": 0.5, "churn_rate": 10.0, "roas": 7.0}
        report = await insight_engine.generate_insights(metrics, use_llm=False)
        assert report.executive_summary != ""

    @pytest.mark.asyncio
    async def test_no_insights_for_healthy_metrics(self, insight_engine):
        metrics = {
            "ctr": 3.0,
            "conversion_rate": 5.0,
            "churn_rate": 2.0,
            "roas": 4.0,
            "ltv_cac_ratio": 5.0,
            "bounce_rate": 35.0,
            "email_open_rate": 25.0,
        }
        report = await insight_engine.generate_insights(metrics, use_llm=False)
        # Healthy metrics should produce few or no warnings
        criticals = [i for i in report.insights if i.severity == "critical"]
        assert len(criticals) == 0

    @pytest.mark.asyncio
    async def test_insights_have_actions(self, insight_engine):
        metrics = {"ctr": 0.3, "bounce_rate": 75.0}
        report = await insight_engine.generate_insights(metrics, use_llm=False)
        for insight in report.insights:
            assert len(insight.suggested_actions) > 0


# ==================================================================
# Anomaly Detection Engine Tests
# ==================================================================

class TestAnomalyDetectionEngine:
    """Tests for the anomaly detection engine."""

    def test_z_score_anomaly(self, anomaly_engine):
        current = {"ctr": 10.0}
        history = [{"ctr": 2.0 + i * 0.1} for i in range(15)]
        report = anomaly_engine.detect_anomalies(current, history)
        assert report.anomaly_count > 0

    def test_no_anomaly_for_normal_values(self, anomaly_engine):
        current = {"ctr": 3.0}
        history = [{"ctr": 3.0 + (i % 3) * 0.05} for i in range(15)]
        report = anomaly_engine.detect_anomalies(current, history, methods=["z_score"])
        # Should have few or no anomalies with z_score method on stable data
        assert report.critical_count == 0

    def test_pct_change_anomaly(self, anomaly_engine):
        current = {"revenue": 200.0}
        history = [{"revenue": 100.0} for _ in range(10)]
        report = anomaly_engine.detect_anomalies(
            current, history, methods=["pct_change"]
        )
        assert report.anomaly_count > 0

    def test_iqr_anomaly(self, anomaly_engine):
        current = {"sessions": 1000.0}
        history = [{"sessions": float(100 + i * 5)} for i in range(20)]
        report = anomaly_engine.detect_anomalies(
            current, history, methods=["iqr"]
        )
        assert report.anomaly_count > 0

    def test_custom_thresholds(self):
        thresholds = AnomalyThresholds(
            z_score_warning=1.5,
            z_score_critical=2.0,
            pct_change_warning=20.0,
        )
        engine = AnomalyDetectionEngine(thresholds=thresholds)
        current = {"ctr": 5.0}
        history = [{"ctr": 2.0} for _ in range(15)]
        report = engine.detect_anomalies(current, history)
        assert report.anomaly_count > 0

    def test_insufficient_history(self, anomaly_engine):
        current = {"ctr": 10.0}
        history = [{"ctr": 2.0}]  # Only 1 point
        report = anomaly_engine.detect_anomalies(current, history)
        assert report.total_metrics_checked == 0

    def test_anomaly_severity_levels(self, anomaly_engine):
        current = {"metric_a": 100.0, "metric_b": 5.0}
        history = [{"metric_a": 10.0, "metric_b": 4.5} for _ in range(15)]
        report = anomaly_engine.detect_anomalies(current, history)
        severities = {a.severity for a in report.anomalies}
        # metric_a should be critical (10x deviation)
        assert "critical" in severities

    def test_deduplication(self, anomaly_engine):
        current = {"ctr": 50.0}
        history = [{"ctr": 2.0} for _ in range(15)]
        report = anomaly_engine.detect_anomalies(current, history)
        # Should have at most 1 anomaly per metric after dedup
        metric_counts = {}
        for a in report.anomalies:
            metric_counts[a.metric] = metric_counts.get(a.metric, 0) + 1
        for count in metric_counts.values():
            assert count == 1


# ==================================================================
# Cohort Analysis Engine Tests
# ==================================================================

class TestCohortAnalysisEngine:
    """Tests for the cohort analysis engine."""

    def test_acquisition_cohort(self, cohort_engine, sample_cohort_events):
        defn = CohortDefinition(
            cohort_type="acquisition",
            period="month",
            retention_event="purchase",
            num_periods=6,
        )
        result = cohort_engine.analyze(sample_cohort_events, defn)
        assert result.cohort_type == "acquisition"
        assert len(result.cohort_labels) > 0
        assert len(result.retention_matrix) == len(result.cohort_labels)
        assert len(result.cohort_sizes) == len(result.cohort_labels)

    def test_behavioral_cohort(self, cohort_engine, sample_cohort_events):
        defn = CohortDefinition(
            cohort_type="behavioral",
            period="month",
            retention_event="purchase",
            num_periods=6,
        )
        result = cohort_engine.analyze(sample_cohort_events, defn)
        assert result.cohort_type == "behavioral"
        assert len(result.cohort_labels) > 0

    def test_revenue_cohort(self, cohort_engine, sample_cohort_events):
        defn = CohortDefinition(
            cohort_type="revenue",
            period="month",
            retention_event="purchase",
            num_periods=6,
        )
        result = cohort_engine.analyze(sample_cohort_events, defn)
        assert result.cohort_type == "revenue"

    def test_retention_matrix_values(self, cohort_engine, sample_cohort_events):
        defn = CohortDefinition(num_periods=6)
        result = cohort_engine.analyze(sample_cohort_events, defn)
        for row in result.retention_matrix:
            for val in row:
                assert 0 <= val <= 100

    def test_summary_statistics(self, cohort_engine, sample_cohort_events):
        defn = CohortDefinition(num_periods=6)
        result = cohort_engine.analyze(sample_cohort_events, defn)
        assert "total_customers" in result.summary
        assert "total_cohorts" in result.summary
        assert result.summary["total_customers"] > 0

    def test_ltv_by_cohort(self, cohort_engine, sample_cohort_events):
        defn = CohortDefinition(num_periods=6)
        result = cohort_engine.analyze(sample_cohort_events, defn)
        assert len(result.ltv_by_cohort) == len(result.cohort_labels)

    def test_weekly_period(self, cohort_engine, sample_cohort_events):
        defn = CohortDefinition(period="week", num_periods=8)
        result = cohort_engine.analyze(sample_cohort_events, defn)
        assert result.period == "week"


# ==================================================================
# Benchmarking Engine Tests
# ==================================================================

class TestBenchmarkingEngine:
    """Tests for the competitive benchmarking engine."""

    def test_saas_benchmarks(self, benchmarking_engine):
        metrics = {"ctr": 3.5, "conversion_rate": 4.0, "cac": 150.0, "roas": 5.0}
        report = benchmarking_engine.compare(metrics, industry="saas")
        assert report.industry == "saas"
        assert len(report.comparisons) > 0
        assert 0 <= report.overall_score <= 100

    def test_ecommerce_benchmarks(self, benchmarking_engine):
        metrics = {"ctr": 2.0, "conversion_rate": 3.0}
        report = benchmarking_engine.compare(metrics, industry="ecommerce")
        assert report.industry == "ecommerce"

    def test_b2b_benchmarks(self, benchmarking_engine):
        metrics = {"ctr": 2.5, "lead_to_mql_rate": 20.0}
        report = benchmarking_engine.compare(metrics, industry="b2b")
        assert report.industry == "b2b"

    def test_strengths_and_weaknesses(self, benchmarking_engine):
        metrics = {"ctr": 6.0, "cac": 500.0}  # Great CTR, terrible CAC
        report = benchmarking_engine.compare(metrics, industry="saas")
        assert len(report.strengths) > 0 or len(report.weaknesses) > 0

    def test_percentile_rank(self, benchmarking_engine):
        metrics = {"ctr": 6.0}  # Best-in-class
        report = benchmarking_engine.compare(metrics, industry="saas")
        for c in report.comparisons:
            if c.metric == "ctr":
                assert c.percentile_rank >= 75

    def test_assessment_categories(self, benchmarking_engine):
        metrics = {"ctr": 0.5, "roas": 12.0}
        report = benchmarking_engine.compare(metrics, industry="saas")
        assessments = {c.assessment for c in report.comparisons}
        assert len(assessments) > 0

    def test_supported_industries(self, benchmarking_engine):
        industries = benchmarking_engine.get_supported_industries()
        assert "saas" in industries
        assert "ecommerce" in industries
        assert "b2b" in industries

    def test_custom_benchmarks(self, benchmarking_engine):
        benchmarking_engine.add_custom_benchmarks("custom_industry", {
            "ctr": (3.0, 2.0, 4.0, 7.0),
        })
        metrics = {"ctr": 5.0}
        report = benchmarking_engine.compare(metrics, industry="custom_industry")
        assert report.industry == "custom_industry"
        assert len(report.comparisons) == 1

    def test_lower_is_better_metrics(self, benchmarking_engine):
        metrics = {"cac": 30.0}  # Very low CAC (good)
        report = benchmarking_engine.compare(metrics, industry="saas")
        for c in report.comparisons:
            if c.metric == "cac":
                assert c.assessment in ("above_average", "best_in_class")


# ==================================================================
# Export Engine Tests
# ==================================================================

class TestExportEngine:
    """Tests for the report export engine."""

    def test_csv_export(self, export_engine):
        data = {
            "metrics": {"ctr": 3.0, "roas": 5.0, "revenue": 50000},
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ExportConfig(format="csv", output_dir=tmpdir)
            result = export_engine.export(data, config)
            assert result.success is True
            assert result.format == "csv"
            assert result.file_path is not None
            assert os.path.exists(result.file_path)
            assert result.file_size_bytes > 0

    def test_json_export(self, export_engine):
        data = {
            "metrics": {"ctr": 3.0},
            "forecast": {"predictions": [{"date": "2025-01-01", "predicted": 100}]},
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ExportConfig(format="json", output_dir=tmpdir)
            result = export_engine.export(data, config)
            assert result.success is True
            assert result.format == "json"
            # Verify JSON is valid
            with open(result.file_path) as f:
                parsed = json.load(f)
            assert "data" in parsed

    def test_pdf_export(self, export_engine):
        data = {
            "metrics": {"ctr": 3.0, "roas": 5.0},
            "executive_summary": "Performance is strong this period.",
            "insights": [
                {
                    "severity": "positive",
                    "title": "Strong ROAS",
                    "narrative": "ROAS exceeds benchmark.",
                    "suggested_actions": ["Scale budget"],
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ExportConfig(format="pdf", output_dir=tmpdir)
            result = export_engine.export(data, config)
            assert result.success is True
            assert result.format == "pdf"
            assert result.file_path.endswith(".pdf")
            assert result.file_size_bytes > 0

    def test_csv_with_anomalies(self, export_engine):
        data = {
            "metrics": {"ctr": 3.0},
            "anomalies": [
                {"metric": "ctr", "severity": "warning", "current_value": 10, "expected_value": 3, "message": "High CTR"}
            ],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ExportConfig(format="csv", output_dir=tmpdir)
            result = export_engine.export(data, config)
            assert result.success is True

    def test_export_with_attribution(self, export_engine):
        data = {
            "metrics": {},
            "attribution": {
                "channel_scores": {"Email": 500, "Social": 300},
                "channel_conversions": {"Email": 10, "Social": 6},
                "channel_roas": {"Email": 5.0, "Social": 3.0},
            },
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ExportConfig(format="csv", output_dir=tmpdir)
            result = export_engine.export(data, config)
            assert result.success is True


# ==================================================================
# Main Module Integration Tests
# ==================================================================

class TestAnalyticsReportingModule:
    """Integration tests for the main analytics module."""

    @pytest.mark.asyncio
    async def test_get_dashboard(self, module):
        result = await module.get_dashboard()
        assert "metrics" in result
        assert "charts" in result
        assert "metadata" in result
        # Should have 30+ scalar metrics
        scalar = {k: v for k, v in result["metrics"].items() if not isinstance(v, dict)}
        assert len(scalar) >= 30

    @pytest.mark.asyncio
    async def test_get_dashboard_with_params(self, module):
        result = await module.get_dashboard(params={"days": 7})
        assert result["metadata"]["period_days"] == 7

    @pytest.mark.asyncio
    async def test_get_forecast(self, module):
        result = await module.get_forecast("revenue", 30)
        assert "forecast" in result
        forecast = result["forecast"]
        assert forecast["metric"] == "revenue"
        assert forecast["horizon_days"] == 30
        assert len(forecast["predictions"]) == 30
        assert forecast["method"] in ForecastingEngine.SUPPORTED_METHODS + ["fallback_constant"]

    @pytest.mark.asyncio
    async def test_get_forecast_with_method(self, module):
        result = await module.get_forecast("leads", 14, method="linear_trend")
        assert result["forecast"]["method"] == "linear_trend"

    @pytest.mark.asyncio
    async def test_get_attribution_all_models(self, module):
        result = await module.get_attribution(model="all")
        assert len(result) == 5
        for model_name in AttributionEngine.SUPPORTED_MODELS:
            assert model_name in result

    @pytest.mark.asyncio
    async def test_get_attribution_single_model(self, module):
        result = await module.get_attribution(model="linear")
        assert "linear" in result

    @pytest.mark.asyncio
    async def test_get_insights(self, module):
        result = await module.get_insights(use_llm=False)
        assert "insight_report" in result
        report = result["insight_report"]
        assert "executive_summary" in report
        assert "insights" in report
        assert report["method"] == "rule_based"

    @pytest.mark.asyncio
    async def test_detect_anomalies(self, module):
        result = await module.detect_anomalies()
        assert "anomaly_report" in result
        report = result["anomaly_report"]
        assert "anomalies" in report
        assert "total_metrics_checked" in report

    @pytest.mark.asyncio
    async def test_get_cohort_analysis(self, module):
        result = await module.get_cohort_analysis()
        assert "cohort_labels" in result
        assert "retention_matrix" in result
        assert "summary" in result

    @pytest.mark.asyncio
    async def test_get_benchmarks(self, module):
        result = await module.get_benchmarks(industry="saas")
        assert "industry" in result
        assert result["industry"] == "saas"
        assert "overall_score" in result
        assert "comparisons" in result

    @pytest.mark.asyncio
    async def test_record_experiment(self, module):
        variants = [
            {"name": "Control", "sample_size": 1000, "conversions": 50},
            {"name": "Variant A", "sample_size": 1000, "conversions": 70},
        ]
        result = await module.record_experiment("exp-001", variants)
        assert "experiment_results" in result
        exp = result["experiment_results"]
        assert exp["id"] == "exp-001"
        assert len(exp["variants"]) == 2
        # Check enhanced fields
        assert "p_value" in exp["variants"][0]
        assert "confidence_interval" in exp["variants"][0]
        assert "statistical_power" in exp["variants"][0]

    @pytest.mark.asyncio
    async def test_record_experiment_insufficient_variants(self, module):
        result = await module.record_experiment("exp-002", [{"name": "Only one"}])
        assert "error" in result["experiment_results"]

    @pytest.mark.asyncio
    async def test_record_experiment_significance(self, module):
        variants = [
            {"name": "Control", "sample_size": 10000, "conversions": 500},
            {"name": "Variant A", "sample_size": 10000, "conversions": 700},
        ]
        result = await module.record_experiment("exp-003", variants)
        exp = result["experiment_results"]
        variant_a = [v for v in exp["variants"] if v["name"] == "Variant A"][0]
        assert variant_a["is_significant"] is True

    @pytest.mark.asyncio
    async def test_export_report_pdf(self, module):
        result = await module.export_report(format="pdf", include_all=False)
        assert result["success"] is True
        assert result["format"] == "pdf"

    @pytest.mark.asyncio
    async def test_export_report_csv(self, module):
        result = await module.export_report(format="csv", include_all=False)
        assert result["success"] is True
        assert result["format"] == "csv"

    @pytest.mark.asyncio
    async def test_export_report_json(self, module):
        result = await module.export_report(format="json", include_all=False)
        assert result["success"] is True
        assert result["format"] == "json"

    @pytest.mark.asyncio
    async def test_kpi_catalog(self, module):
        catalog = module.get_kpi_catalog()
        assert len(catalog) >= 30

    @pytest.mark.asyncio
    async def test_supported_industries(self, module):
        industries = module.get_supported_industries()
        assert "saas" in industries

    # Handler tests
    @pytest.mark.asyncio
    async def test_handle_dashboard(self, module):
        result = await module.handle("Show me the dashboard metrics", {})
        assert "response" in result
        assert "KPI" in result["response"] or "Metric" in result["response"]

    @pytest.mark.asyncio
    async def test_handle_forecast(self, module):
        result = await module.handle("Forecast our revenue for next month", {})
        assert "response" in result

    @pytest.mark.asyncio
    async def test_handle_attribution(self, module):
        result = await module.handle("Show me channel attribution", {})
        assert "response" in result

    @pytest.mark.asyncio
    async def test_handle_anomaly(self, module):
        result = await module.handle("Check for anomalies in our metrics", {})
        assert "response" in result

    @pytest.mark.asyncio
    async def test_handle_cohort(self, module):
        result = await module.handle("Show retention cohort analysis", {})
        assert "response" in result

    @pytest.mark.asyncio
    async def test_handle_benchmark(self, module):
        result = await module.handle("How do we compare to industry benchmarks?", {})
        assert "response" in result

    @pytest.mark.asyncio
    async def test_handle_insights(self, module):
        result = await module.handle("Give me insights and recommendations", {})
        assert "response" in result

    @pytest.mark.asyncio
    async def test_handle_export(self, module):
        result = await module.handle("Export a PDF report", {})
        assert "response" in result

    def test_generate_chart_data(self, module):
        metrics = {"impressions": 100000, "clicks": 5000, "ctr": 5.0, "activation_rate": 40.0, "retention_rate": 95.0, "roas": 5.0, "viral_coefficient": 0.5}
        charts = module._generate_chart_data(30, metrics)
        assert len(charts) == 5
        assert charts[0]["type"] == "line"
        assert charts[1]["type"] == "bar"
        assert charts[2]["type"] == "funnel"
