"""
Pydantic schemas for API request/response validation.
"""

from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel, EmailStr


# ── Auth ──────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenBalance(BaseModel):
    balance: int
    tier: str
    reset_date: Optional[datetime] = None


# ── Chat / Brain ──────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    context: Optional[dict] = None


class ChatResponse(BaseModel):
    reply: str
    conversation_id: str
    module_used: Optional[str] = None
    tokens_used: int = 0


# ── Business Analysis ─────────────────────────────────────────────────

class MarketAnalysisRequest(BaseModel):
    query: str
    context: Optional[dict] = None


class SWOTRequest(BaseModel):
    subject: str
    context: Optional[dict] = None


class PESTELRequest(BaseModel):
    subject: str
    context: Optional[dict] = None


class CompetitorAnalysisRequest(BaseModel):
    company_names: list[str]
    context: Optional[dict] = None


class PersonaRequest(BaseModel):
    data_source: str = "default"
    num_personas: int = 3
    context: Optional[dict] = None


class AnalysisResponse(BaseModel):
    insights: Optional[list[dict]] = None
    analysis: Optional[dict] = None
    personas: Optional[list[dict]] = None
    sources: Optional[list[str]] = None


# ── Creative & Design ─────────────────────────────────────────────────

class CopyGenerationRequest(BaseModel):
    brief: str
    tone: Optional[str] = None
    copy_format: Optional[str] = None
    length: Optional[int] = None
    language: Optional[str] = None
    brand_name: Optional[str] = None
    context: Optional[dict] = None


class ImageGenerationRequest(BaseModel):
    description: str
    style: Optional[str] = None
    brand_name: Optional[str] = None
    context: Optional[dict] = None


class ABTestRequest(BaseModel):
    base_copy: str
    num_variants: int = 4
    brand_name: Optional[str] = None
    context: Optional[dict] = None


class ContentScheduleRequest(BaseModel):
    events: list[dict]
    context: Optional[dict] = None


class ContentCalendarRequest(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    channels: Optional[list[str]] = None
    industry: Optional[str] = None
    product_launches: Optional[list[dict]] = None
    custom_events: Optional[list[dict]] = None
    brand_name: Optional[str] = None
    context: Optional[dict] = None


class BrandVoiceLearnRequest(BaseModel):
    brand_name: str
    samples: list[str]


class BrandVoiceCheckRequest(BaseModel):
    brand_name: str
    copy_text: str


class TranslationRequest(BaseModel):
    copy_text: str
    target_language: str
    source_language: str = "en"
    formality: Optional[str] = None


class BatchTranslationRequest(BaseModel):
    copy_text: str
    target_languages: list[str]
    source_language: str = "en"


class CreativeResponse(BaseModel):
    content: Optional[str] = None
    alternatives: Optional[list[str]] = None
    schedule: Optional[list[dict]] = None
    image_url: Optional[str] = None
    metadata: Optional[dict] = None


class ABTestResponse(BaseModel):
    base_copy: str
    num_variants: int = 0
    variants: Optional[list[dict]] = None
    recommended_variant: Optional[dict] = None
    scoring_dimensions: Optional[list[dict]] = None
    summary: Optional[str] = None


class ContentCalendarResponse(BaseModel):
    calendar: Optional[list[dict]] = None
    date_range: Optional[dict] = None
    channels: Optional[list[str]] = None
    events_included: Optional[list[dict]] = None
    content_mix: Optional[dict] = None
    posting_guidelines: Optional[dict] = None
    total_entries: int = 0


class BrandVoiceResponse(BaseModel):
    profile: Optional[dict] = None
    prompt_fragment: Optional[str] = None
    message: Optional[str] = None
    scores: Optional[dict] = None
    suggestions: Optional[list[str]] = None
    revised_copy: Optional[str] = None


class TranslationResponse(BaseModel):
    original: Optional[str] = None
    translated: Optional[str] = None
    source_language: Optional[str] = None
    target_language: Optional[str] = None
    formality: Optional[str] = None
    translations: Optional[dict] = None
    languages_count: int = 0


class CapabilitiesResponse(BaseModel):
    tones: Optional[list[str]] = None
    formats: Optional[list[str]] = None
    languages: Optional[list[dict]] = None
    brand_profiles: Optional[list[str]] = None


# ── CRM & Campaign ───────────────────────────────────────────────────

class LeadUpdateRequest(BaseModel):
    lead_id: str
    attributes: dict


class LeadImportRequest(BaseModel):
    leads: list[dict]


class CampaignCreateRequest(BaseModel):
    name: str
    audience_query: Optional[dict] = None
    content: Optional[dict] = None
    schedule: Optional[dict] = None
    channel: str = "email"


class CampaignPredictRequest(BaseModel):
    avg_order_value: float = 50.0


class WorkflowTriggerRequest(BaseModel):
    workflow_id: str
    lead_id: str


class WorkflowAdvanceRequest(BaseModel):
    workflow_id: str
    lead_id: str
    condition_results: Optional[dict] = None


class ComplianceCheckRequest(BaseModel):
    message: str
    channel: str


class ConsentRequest(BaseModel):
    lead_id: str
    channel: str
    consent_type: str = "express"
    source: str = "web_form"


class ConsentWithdrawRequest(BaseModel):
    lead_id: str
    channel: str


class DataSubjectRequestSchema(BaseModel):
    lead_id: str
    right: str  # access, erasure, export, portability, restriction, objection


class PreSendCheckRequest(BaseModel):
    lead_id: str
    channel: str
    message: str


class JourneyInitRequest(BaseModel):
    lead_id: str
    stage: str = "awareness"


class TouchpointRequest(BaseModel):
    lead_id: str
    channel: str
    action: str
    details: Optional[dict] = None


class JourneyAdvanceRequest(BaseModel):
    lead_id: str
    target_stage: Optional[str] = None


class SegmentCreateRequest(BaseModel):
    name: str
    rules: list[dict]
    logic: str = "and"
    description: str = ""


class SegmentEvaluateRequest(BaseModel):
    lead_id: Optional[str] = None


class ABTestCreateRequest(BaseModel):
    campaign_id: str
    name: str
    variants: list[dict]
    primary_metric: str = "click_rate"
    confidence_threshold: float = 95.0


class ABTestEventRequest(BaseModel):
    variant_id: str
    event_type: str  # send, open, click, conversion, unsubscribe
    count: int = 1
    revenue: float = 0.0


class SampleSizeRequest(BaseModel):
    baseline_rate: float
    minimum_detectable_effect: float = 0.1


class CRMResponse(BaseModel):
    status: str
    details: Optional[dict] = None
    logs: Optional[list[str]] = None


# ── Analytics & Reporting ─────────────────────────────────────────────

class DashboardRequest(BaseModel):
    params: Optional[dict] = None
    context: Optional[dict] = None


class ForecastRequest(BaseModel):
    metric: str
    horizon: int = 30
    params: Optional[dict] = None
    method: str = "auto"


class ExperimentRecordRequest(BaseModel):
    experiment_id: str
    variants: list[dict]
    results: Optional[dict] = None


class AttributionRequest(BaseModel):
    journeys: Optional[list[dict]] = None
    model: str = "all"
    decay_half_life_days: float = 7.0


class InsightRequest(BaseModel):
    metrics: Optional[dict] = None
    period_description: str = "last 30 days"
    use_llm: bool = True


class AnomalyRequest(BaseModel):
    current_metrics: Optional[dict] = None
    historical_metrics: Optional[list[dict]] = None


class CohortRequest(BaseModel):
    events: Optional[list[dict]] = None
    cohort_type: str = "acquisition"
    period: str = "month"
    retention_event: str = "purchase"
    num_periods: int = 12


class BenchmarkRequest(BaseModel):
    metrics: Optional[dict] = None
    industry: str = "saas"


class ExportRequest(BaseModel):
    format: str = "pdf"
    include_all: bool = True
    config: Optional[dict] = None


class AnalyticsResponse(BaseModel):
    metrics: Optional[dict] = None
    charts: Optional[list[dict]] = None
    forecast: Optional[dict] = None
    experiment_results: Optional[dict] = None
    attribution: Optional[dict] = None
    insight_report: Optional[dict] = None
    anomaly_report: Optional[dict] = None
    cohort_analysis: Optional[dict] = None
    benchmarks: Optional[dict] = None
    export_result: Optional[dict] = None


# ── Memory ────────────────────────────────────────────────────────────

class MemoryStoreRequest(BaseModel):
    file_path: str
    content: str


class MemoryRetrieveRequest(BaseModel):
    query: str
    k: int = 5


class MemoryResponse(BaseModel):
    status: str
    data: Optional[Any] = None
