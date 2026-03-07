# Analytics & Reporting Module — Comprehensive Marketing Intelligence
from .module import AnalyticsReportingModule
from .engines.kpi_engine import KPIEngine, RawMetricsInput, KPI_CATALOG
from .engines.forecasting_engine import ForecastingEngine, TimeSeriesPoint, ForecastResult
from .engines.attribution_engine import (
    AttributionEngine,
    Touchpoint,
    CustomerJourney,
    AttributionResult,
)
from .engines.insight_engine import InsightEngine, Insight, InsightReport
from .engines.anomaly_engine import (
    AnomalyDetectionEngine,
    AnomalyThresholds,
    Anomaly,
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

__all__ = [
    "AnalyticsReportingModule",
    # KPI
    "KPIEngine",
    "RawMetricsInput",
    "KPI_CATALOG",
    # Forecasting
    "ForecastingEngine",
    "TimeSeriesPoint",
    "ForecastResult",
    # Attribution
    "AttributionEngine",
    "Touchpoint",
    "CustomerJourney",
    "AttributionResult",
    # Insights
    "InsightEngine",
    "Insight",
    "InsightReport",
    # Anomaly Detection
    "AnomalyDetectionEngine",
    "AnomalyThresholds",
    "Anomaly",
    "AnomalyReport",
    # Cohort Analysis
    "CohortAnalysisEngine",
    "CustomerEvent",
    "CohortDefinition",
    "CohortResult",
    # Benchmarking
    "BenchmarkingEngine",
    "BenchmarkReport",
    # Export
    "ExportEngine",
    "ExportConfig",
    "EmailSchedule",
    "ExportResult",
]
