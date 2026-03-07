"""
Analytics & Reporting API endpoints.

GET/POST /analytics/dashboard     - Get dashboard metrics and charts (30+ KPIs)
POST     /analytics/forecast      - Generate time-series metric forecasts
POST     /analytics/experiment    - Record and analyse A/B experiments
POST     /analytics/attribution   - Run multi-touch attribution models
POST     /analytics/insights      - Generate automated insights
POST     /analytics/anomalies     - Detect metric anomalies
POST     /analytics/cohort        - Perform cohort analysis
POST     /analytics/benchmarks    - Compare against industry benchmarks
POST     /analytics/export        - Export reports (PDF, CSV, JSON)
GET      /analytics/kpi-catalog   - List all available KPIs
GET      /analytics/industries    - List supported benchmark industries
"""

from fastapi import APIRouter, Depends

from ..db.schemas import (
    DashboardRequest,
    ForecastRequest,
    ExperimentRecordRequest,
    AttributionRequest,
    InsightRequest,
    AnomalyRequest,
    CohortRequest,
    BenchmarkRequest,
    ExportRequest,
    AnalyticsResponse,
)
from ..modules.analytics_reporting import AnalyticsReportingModule

router = APIRouter(prefix="/analytics", tags=["Analytics & Reporting"])

_module = AnalyticsReportingModule()


def get_module() -> AnalyticsReportingModule:
    return _module


# ── Dashboard ────────────────────────────────────────────────────────

@router.get("/dashboard", response_model=AnalyticsResponse)
async def get_dashboard(
    module: AnalyticsReportingModule = Depends(get_module),
):
    """Retrieve dashboard metrics (30+ KPIs) and chart data."""
    result = await module.get_dashboard()
    return AnalyticsResponse(
        metrics=result.get("metrics"),
        charts=result.get("charts"),
    )


@router.post("/dashboard", response_model=AnalyticsResponse)
async def get_dashboard_filtered(
    request: DashboardRequest,
    module: AnalyticsReportingModule = Depends(get_module),
):
    """Retrieve filtered dashboard metrics and chart data."""
    result = await module.get_dashboard(params=request.params, context=request.context)
    return AnalyticsResponse(
        metrics=result.get("metrics"),
        charts=result.get("charts"),
    )


# ── Forecasting ──────────────────────────────────────────────────────

@router.post("/forecast", response_model=AnalyticsResponse)
async def get_forecast(
    request: ForecastRequest,
    module: AnalyticsReportingModule = Depends(get_module),
):
    """Generate a time-series forecast for a specified metric."""
    result = await module.get_forecast(
        metric=request.metric,
        horizon=request.horizon,
        params=request.params,
        method=request.method,
    )
    return AnalyticsResponse(forecast=result.get("forecast"))


# ── A/B Experiments ──────────────────────────────────────────────────

@router.post("/experiment", response_model=AnalyticsResponse)
async def record_experiment(
    request: ExperimentRecordRequest,
    module: AnalyticsReportingModule = Depends(get_module),
):
    """Record A/B test results and calculate uplift/significance."""
    result = await module.record_experiment(
        experiment_id=request.experiment_id,
        variants=request.variants,
        results=request.results,
    )
    return AnalyticsResponse(experiment_results=result.get("experiment_results"))


# ── Attribution ──────────────────────────────────────────────────────

@router.post("/attribution", response_model=AnalyticsResponse)
async def get_attribution(
    request: AttributionRequest,
    module: AnalyticsReportingModule = Depends(get_module),
):
    """Run multi-touch attribution models on customer journeys."""
    result = await module.get_attribution(
        journeys=request.journeys,
        model=request.model,
        decay_half_life_days=request.decay_half_life_days,
    )
    return AnalyticsResponse(attribution=result)


# ── Automated Insights ───────────────────────────────────────────────

@router.post("/insights", response_model=AnalyticsResponse)
async def get_insights(
    request: InsightRequest,
    module: AnalyticsReportingModule = Depends(get_module),
):
    """Generate automated insights and action recommendations."""
    result = await module.get_insights(
        metrics=request.metrics,
        period_description=request.period_description,
        use_llm=request.use_llm,
    )
    return AnalyticsResponse(insight_report=result.get("insight_report"))


# ── Anomaly Detection ────────────────────────────────────────────────

@router.post("/anomalies", response_model=AnalyticsResponse)
async def detect_anomalies(
    request: AnomalyRequest,
    module: AnalyticsReportingModule = Depends(get_module),
):
    """Detect anomalies in current metrics vs. historical data."""
    result = await module.detect_anomalies(
        current_metrics=request.current_metrics,
        historical_metrics=request.historical_metrics,
    )
    return AnalyticsResponse(anomaly_report=result.get("anomaly_report"))


# ── Cohort Analysis ──────────────────────────────────────────────────

@router.post("/cohort", response_model=AnalyticsResponse)
async def get_cohort_analysis(
    request: CohortRequest,
    module: AnalyticsReportingModule = Depends(get_module),
):
    """Perform cohort analysis on customer events."""
    result = await module.get_cohort_analysis(
        events=request.events,
        cohort_type=request.cohort_type,
        period=request.period,
        retention_event=request.retention_event,
        num_periods=request.num_periods,
    )
    return AnalyticsResponse(cohort_analysis=result)


# ── Competitive Benchmarks ───────────────────────────────────────────

@router.post("/benchmarks", response_model=AnalyticsResponse)
async def get_benchmarks(
    request: BenchmarkRequest,
    module: AnalyticsReportingModule = Depends(get_module),
):
    """Compare your metrics against industry benchmarks."""
    result = await module.get_benchmarks(
        metrics=request.metrics,
        industry=request.industry,
    )
    return AnalyticsResponse(benchmarks=result)


# ── Export ────────────────────────────────────────────────────────────

@router.post("/export", response_model=AnalyticsResponse)
async def export_report(
    request: ExportRequest,
    module: AnalyticsReportingModule = Depends(get_module),
):
    """Export analytics report in PDF, CSV, or JSON format."""
    result = await module.export_report(
        format=request.format,
        include_all=request.include_all,
    )
    return AnalyticsResponse(export_result=result)


# ── Catalog Endpoints ────────────────────────────────────────────────

@router.get("/kpi-catalog")
async def get_kpi_catalog(
    module: AnalyticsReportingModule = Depends(get_module),
):
    """List all 30+ available KPIs with metadata."""
    return {"kpis": module.get_kpi_catalog(), "total": len(module.get_kpi_catalog())}


@router.get("/industries")
async def get_industries(
    module: AnalyticsReportingModule = Depends(get_module),
):
    """List supported industries for benchmarking."""
    return {"industries": module.get_supported_industries()}
