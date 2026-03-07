"""
CRM & Campaign Management API endpoints.

Lead Management:
  POST /crm/lead              - Create or update a lead
  POST /crm/leads/import      - Bulk import leads
  GET  /crm/leads             - List all leads
  GET  /crm/lead/{lead_id}    - Get a single lead

Lead Scoring:
  POST /crm/lead/{lead_id}/score  - Score a specific lead
  POST /crm/leads/score-all      - Score all leads
  GET  /crm/scoring/metrics       - Get scoring model metrics

Campaign Management:
  POST /crm/campaign              - Create a campaign
  GET  /crm/campaigns             - List all campaigns
  POST /crm/campaign/{id}/predict - Predict campaign performance

Workflow Automation:
  POST /crm/workflow              - Trigger a workflow
  POST /crm/workflow/advance      - Advance a workflow step
  GET  /crm/workflows             - List available workflows

Customer Journey:
  POST /crm/journey/init          - Initialise a journey
  POST /crm/journey/touchpoint    - Record a touchpoint
  POST /crm/journey/advance       - Advance journey stage
  GET  /crm/journey/{lead_id}     - Get lead journey
  GET  /crm/journey/funnel        - Get funnel metrics

Segmentation:
  POST /crm/segment               - Create a segment
  POST /crm/segment/evaluate      - Evaluate leads against segments
  POST /crm/segment/auto          - Auto-segment leads
  GET  /crm/segments              - List all segments
  GET  /crm/segment/templates     - List segment templates

Compliance:
  POST /crm/compliance            - Check message compliance
  POST /crm/consent               - Record consent
  POST /crm/consent/withdraw      - Withdraw consent
  GET  /crm/consent/{lead_id}     - Get consent status
  POST /crm/gdpr/request          - Handle data subject request
  POST /crm/compliance/pre-send   - Pre-send compliance gate
  GET  /crm/compliance/audit-log  - Get audit log

A/B Testing:
  POST /crm/ab-test               - Create an A/B test
  POST /crm/ab-test/{id}/start    - Start a test
  POST /crm/ab-test/{id}/event    - Record a test event
  GET  /crm/ab-test/{id}/analyse  - Analyse test results
  GET  /crm/ab-tests              - List all tests
  POST /crm/ab-test/sample-size   - Calculate sample size
"""

from typing import Optional

from fastapi import APIRouter, Depends

from ..db.schemas import (
    LeadUpdateRequest,
    LeadImportRequest,
    CampaignCreateRequest,
    WorkflowTriggerRequest,
    WorkflowAdvanceRequest,
    ComplianceCheckRequest,
    ConsentRequest,
    ConsentWithdrawRequest,
    DataSubjectRequestSchema,
    PreSendCheckRequest,
    JourneyInitRequest,
    TouchpointRequest,
    JourneyAdvanceRequest,
    SegmentCreateRequest,
    SegmentEvaluateRequest,
    ABTestCreateRequest,
    ABTestEventRequest,
    SampleSizeRequest,
    CampaignPredictRequest,
    CRMResponse,
)
from ..modules.crm_campaign import CRMCampaignModule

router = APIRouter(prefix="/crm", tags=["CRM & Campaign"])

_module = CRMCampaignModule()


def get_module() -> CRMCampaignModule:
    return _module


# ── Lead Management ────────────────────────────────────────────────────

@router.post("/lead", response_model=CRMResponse)
async def update_lead(
    request: LeadUpdateRequest,
    module: CRMCampaignModule = Depends(get_module),
):
    """Create or update a lead in the CRM."""
    result = await module.update_lead(request.lead_id, request.attributes)
    return CRMResponse(**result)


@router.post("/leads/import", response_model=CRMResponse)
async def import_leads(
    request: LeadImportRequest,
    module: CRMCampaignModule = Depends(get_module),
):
    """Bulk import leads into the CRM."""
    result = await module.import_leads(request.leads)
    return CRMResponse(**result)


@router.get("/leads")
async def list_leads(module: CRMCampaignModule = Depends(get_module)):
    """List all leads in the system."""
    return {"leads": module.get_leads()}


@router.get("/lead/{lead_id}")
async def get_lead(lead_id: str, module: CRMCampaignModule = Depends(get_module)):
    """Get a single lead by ID."""
    lead = module.get_lead(lead_id)
    if lead:
        return {"lead": lead}
    return {"error": "Lead not found"}


# ── Lead Scoring ───────────────────────────────────────────────────────

@router.post("/lead/{lead_id}/score", response_model=CRMResponse)
async def score_lead(
    lead_id: str,
    module: CRMCampaignModule = Depends(get_module),
):
    """Score a specific lead using the ML scoring model."""
    result = await module.score_lead(lead_id)
    return CRMResponse(**result)


@router.post("/leads/score-all", response_model=CRMResponse)
async def score_all_leads(module: CRMCampaignModule = Depends(get_module)):
    """Score all leads in the CRM."""
    result = await module.score_all_leads()
    return CRMResponse(**result)


@router.get("/scoring/metrics")
async def get_scoring_metrics(module: CRMCampaignModule = Depends(get_module)):
    """Get lead scoring model metrics."""
    return module.lead_scorer.get_model_metrics()


# ── Campaign Management ────────────────────────────────────────────────

@router.post("/campaign", response_model=CRMResponse)
async def create_campaign(
    request: CampaignCreateRequest,
    module: CRMCampaignModule = Depends(get_module),
):
    """Create and schedule a marketing campaign."""
    result = await module.create_campaign(
        name=request.name,
        audience_query=request.audience_query,
        content=request.content,
        schedule=request.schedule,
        channel=request.channel,
    )
    return CRMResponse(**result)


@router.get("/campaigns")
async def list_campaigns(module: CRMCampaignModule = Depends(get_module)):
    """List all campaigns in the system."""
    return {"campaigns": module.get_campaigns()}


@router.post("/campaign/{campaign_id}/predict", response_model=CRMResponse)
async def predict_campaign(
    campaign_id: str,
    request: CampaignPredictRequest,
    module: CRMCampaignModule = Depends(get_module),
):
    """Predict campaign performance before launch."""
    result = await module.predict_campaign_performance(
        campaign_id, request.avg_order_value
    )
    return CRMResponse(**result)


# ── Workflow Automation ────────────────────────────────────────────────

@router.post("/workflow", response_model=CRMResponse)
async def trigger_workflow(
    request: WorkflowTriggerRequest,
    module: CRMCampaignModule = Depends(get_module),
):
    """Trigger a predefined workflow for a lead."""
    result = await module.trigger_workflow(request.workflow_id, request.lead_id)
    return CRMResponse(**result)


@router.post("/workflow/advance", response_model=CRMResponse)
async def advance_workflow(
    request: WorkflowAdvanceRequest,
    module: CRMCampaignModule = Depends(get_module),
):
    """Advance a workflow to the next step."""
    result = await module.advance_workflow(
        request.workflow_id, request.lead_id, request.condition_results
    )
    return CRMResponse(**result)


@router.get("/workflows")
async def list_workflows(module: CRMCampaignModule = Depends(get_module)):
    """List all available workflow templates."""
    return {"workflows": module.workflow_engine.get_available_workflows()}


# ── Customer Journey ───────────────────────────────────────────────────

@router.post("/journey/init", response_model=CRMResponse)
async def init_journey(
    request: JourneyInitRequest,
    module: CRMCampaignModule = Depends(get_module),
):
    """Initialise a customer journey for a lead."""
    result = module.initialise_journey(request.lead_id, request.stage)
    return CRMResponse(**result)


@router.post("/journey/touchpoint", response_model=CRMResponse)
async def record_touchpoint(
    request: TouchpointRequest,
    module: CRMCampaignModule = Depends(get_module),
):
    """Record a touchpoint in the customer journey."""
    result = module.record_touchpoint(
        request.lead_id, request.channel, request.action, request.details
    )
    return CRMResponse(**result)


@router.post("/journey/advance", response_model=CRMResponse)
async def advance_journey(
    request: JourneyAdvanceRequest,
    module: CRMCampaignModule = Depends(get_module),
):
    """Advance a lead to the next journey stage."""
    result = module.advance_journey_stage(request.lead_id, request.target_stage)
    return CRMResponse(**result)


@router.get("/journey/{lead_id}")
async def get_journey(lead_id: str, module: CRMCampaignModule = Depends(get_module)):
    """Get the full customer journey for a lead."""
    journey = module.get_journey(lead_id)
    if journey:
        return {"journey": journey}
    return {"error": "Journey not found"}


@router.get("/journey/funnel/metrics")
async def get_funnel_metrics(module: CRMCampaignModule = Depends(get_module)):
    """Get funnel conversion metrics across all journeys."""
    return module.get_funnel_metrics()


# ── Segmentation ──────────────────────────────────────────────────────

@router.post("/segment", response_model=CRMResponse)
async def create_segment(
    request: SegmentCreateRequest,
    module: CRMCampaignModule = Depends(get_module),
):
    """Create a new segment."""
    result = module.create_segment(
        name=request.name, rules=request.rules,
        logic=request.logic, description=request.description,
    )
    return CRMResponse(**result)


@router.post("/segment/evaluate", response_model=CRMResponse)
async def evaluate_segments(
    request: SegmentEvaluateRequest,
    module: CRMCampaignModule = Depends(get_module),
):
    """Evaluate leads against all segments."""
    result = module.evaluate_segments(request.lead_id)
    return CRMResponse(**result)


@router.post("/segment/auto")
async def auto_segment(module: CRMCampaignModule = Depends(get_module)):
    """Auto-segment all leads by engagement tier."""
    return module.auto_segment_leads()


@router.get("/segments")
async def list_segments(module: CRMCampaignModule = Depends(get_module)):
    """List all segments."""
    return {"segments": module.segmentation_engine.list_segments()}


@router.get("/segment/templates")
async def list_segment_templates(module: CRMCampaignModule = Depends(get_module)):
    """List available segment templates."""
    return {"templates": module.segmentation_engine.get_available_templates()}


# ── Compliance ─────────────────────────────────────────────────────────

@router.post("/compliance", response_model=CRMResponse)
async def check_compliance(
    request: ComplianceCheckRequest,
    module: CRMCampaignModule = Depends(get_module),
):
    """Check whether a message complies with regulations."""
    result = await module.check_compliance(request.message, request.channel)
    return CRMResponse(**result)


@router.post("/consent", response_model=CRMResponse)
async def record_consent(
    request: ConsentRequest,
    module: CRMCampaignModule = Depends(get_module),
):
    """Record consent for a lead on a channel."""
    result = module.record_consent(
        lead_id=request.lead_id,
        channel=request.channel,
        consent_type=request.consent_type,
        source=request.source,
    )
    return CRMResponse(**result)


@router.post("/consent/withdraw", response_model=CRMResponse)
async def withdraw_consent(
    request: ConsentWithdrawRequest,
    module: CRMCampaignModule = Depends(get_module),
):
    """Withdraw consent for a lead on a channel."""
    result = module.withdraw_consent(request.lead_id, request.channel)
    return CRMResponse(**result)


@router.get("/consent/{lead_id}")
async def get_consent_status(
    lead_id: str,
    module: CRMCampaignModule = Depends(get_module),
):
    """Get consent status for a lead."""
    return module.compliance_engine.get_consent_status(lead_id)


@router.post("/gdpr/request", response_model=CRMResponse)
async def handle_dsr(
    request: DataSubjectRequestSchema,
    module: CRMCampaignModule = Depends(get_module),
):
    """Handle a GDPR data subject request."""
    result = module.handle_data_subject_request(request.lead_id, request.right)
    return CRMResponse(**result)


@router.post("/compliance/pre-send", response_model=CRMResponse)
async def pre_send_check(
    request: PreSendCheckRequest,
    module: CRMCampaignModule = Depends(get_module),
):
    """Run a pre-send compliance gate."""
    result = module.pre_send_check(request.lead_id, request.channel, request.message)
    return CRMResponse(status="success", details=result)


@router.get("/compliance/audit-log")
async def get_audit_log(
    lead_id: Optional[str] = None,
    limit: int = 100,
    module: CRMCampaignModule = Depends(get_module),
):
    """Get compliance audit log."""
    return {"audit_log": module.compliance_engine.get_audit_log(lead_id=lead_id, limit=limit)}


# ── A/B Testing ────────────────────────────────────────────────────────

@router.post("/ab-test", response_model=CRMResponse)
async def create_ab_test(
    request: ABTestCreateRequest,
    module: CRMCampaignModule = Depends(get_module),
):
    """Create an A/B test for a campaign."""
    result = module.create_ab_test(
        campaign_id=request.campaign_id,
        name=request.name,
        variants=request.variants,
        primary_metric=request.primary_metric,
        confidence_threshold=request.confidence_threshold,
    )
    return CRMResponse(**result)


@router.post("/ab-test/{test_id}/start", response_model=CRMResponse)
async def start_ab_test(
    test_id: str,
    module: CRMCampaignModule = Depends(get_module),
):
    """Start an A/B test."""
    result = module.ab_testing_engine.start_test(test_id)
    return CRMResponse(**result)


@router.post("/ab-test/{test_id}/event", response_model=CRMResponse)
async def record_ab_event(
    test_id: str,
    request: ABTestEventRequest,
    module: CRMCampaignModule = Depends(get_module),
):
    """Record an event for an A/B test variant."""
    result = module.record_ab_event(
        test_id, request.variant_id, request.event_type,
        count=request.count, revenue=request.revenue,
    )
    return CRMResponse(**result)


@router.get("/ab-test/{test_id}/analyse")
async def analyse_ab_test(
    test_id: str,
    module: CRMCampaignModule = Depends(get_module),
):
    """Analyse an A/B test for statistical significance."""
    return module.analyse_ab_test(test_id)


@router.get("/ab-tests")
async def list_ab_tests(
    campaign_id: Optional[str] = None,
    module: CRMCampaignModule = Depends(get_module),
):
    """List all A/B tests."""
    return {"tests": module.ab_testing_engine.list_tests(campaign_id=campaign_id)}


@router.post("/ab-test/sample-size")
async def calculate_sample_size(
    request: SampleSizeRequest,
    module: CRMCampaignModule = Depends(get_module),
):
    """Calculate required sample size for an A/B test."""
    return module.ab_testing_engine.calculate_sample_size(
        baseline_rate=request.baseline_rate,
        minimum_detectable_effect=request.minimum_detectable_effect,
    )
