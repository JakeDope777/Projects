"""
CRM & Campaign Management Module

Manages leads, orchestrates multi-channel campaigns, automates workflows,
and ensures regulatory compliance (GDPR, CAN-SPAM, CASL).

Sub-modules:
- Lead Scoring: ML-based scoring with feature engineering
- Workflow Automation: Pre-built sequences with event triggers
- Customer Journey Mapping: Stage tracking and funnel analytics
- Smart Segmentation: Rule-based and RFM auto-segmentation
- Campaign Predictor: Pre-launch performance prediction
- Compliance Engine: GDPR rights, consent management, audit logging
- A/B Testing: Statistical significance tracking
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from .lead_scoring import LeadScoringModel, FeatureEngineer
from .workflow_automation import WorkflowEngine, WORKFLOW_TEMPLATES as WF_TEMPLATES
from .journey_mapping import JourneyMapper, JourneyStage
from .segmentation import SegmentationEngine
from .campaign_predictor import CampaignPredictor
from .compliance import ComplianceEngine
from .ab_testing import ABTestingEngine


class CRMCampaignModule:
    """
    Manages customer relationships, campaigns, workflows, and compliance.

    Integrates ML-based lead scoring, workflow automation, customer journey
    mapping, smart segmentation, campaign performance prediction, full
    compliance management, and A/B testing.
    """

    def __init__(
        self,
        crm_clients: Optional[dict] = None,
        integrator=None,
        memory_manager=None,
    ):
        self.crm_clients = crm_clients or {}
        self.integrator = integrator
        self.memory = memory_manager

        # In-memory stores
        self._leads: dict[str, dict] = {}
        self._campaigns: dict[str, dict] = {}

        # Sub-engines
        self.lead_scorer = LeadScoringModel()
        self.workflow_engine = WorkflowEngine()
        self.journey_mapper = JourneyMapper()
        self.segmentation_engine = SegmentationEngine()
        self.campaign_predictor = CampaignPredictor()
        self.compliance_engine = ComplianceEngine()
        self.ab_testing_engine = ABTestingEngine()

    # ── Generic handler ────────────────────────────────────────────────

    async def handle(self, message: str, context: dict) -> dict:
        """Generic handler called by the Brain orchestrator."""
        msg = message.lower()

        if "lead" in msg and "scor" in msg:
            return {"response": "ML-based lead scoring is available. Use /crm/lead/score to score leads."}
        elif "lead" in msg:
            return {"response": "Lead management is ready. Use the /crm/lead endpoint to manage leads."}
        elif "journey" in msg:
            return {"response": "Customer journey mapping is available. Use /crm/journey endpoints."}
        elif "segment" in msg:
            return {"response": "Smart segmentation is available. Use /crm/segment endpoints."}
        elif "a/b" in msg or "ab test" in msg:
            return {"response": "A/B testing is available. Use /crm/ab-test endpoints."}
        elif "predict" in msg:
            return {"response": "Campaign prediction is available. Use /crm/campaign/predict."}
        elif "campaign" in msg:
            return {"response": "Campaign orchestration is ready. Use /crm/campaign to create campaigns."}
        elif "compliance" in msg or "gdpr" in msg or "consent" in msg:
            return {"response": "Compliance management is available. Use /crm/compliance endpoints."}
        elif "workflow" in msg:
            available = ", ".join(WF_TEMPLATES.keys())
            return {"response": f"Available workflows: {available}. Use /crm/workflow to trigger one."}
        else:
            return {
                "response": (
                    "CRM & Campaign module is ready. Available features: "
                    "lead management, ML scoring, workflow automation, "
                    "customer journey mapping, smart segmentation, "
                    "campaign prediction, compliance (GDPR/CAN-SPAM/CASL), "
                    "and A/B testing."
                )
            }

    # ── Lead management ────────────────────────────────────────────────

    async def import_leads(self, leads: list[dict]) -> dict:
        """Bulk import leads into the CRM."""
        imported = 0
        errors = []
        for lead in leads:
            lead_id = lead.get("id") or str(uuid.uuid4())
            try:
                lead["id"] = lead_id
                lead.setdefault("created_at", datetime.now(timezone.utc).isoformat())
                lead["updated_at"] = datetime.now(timezone.utc).isoformat()
                self._leads[lead_id] = lead
                imported += 1
            except Exception as e:
                errors.append({"lead_id": lead_id, "error": str(e)})

        return {
            "status": "success",
            "details": {"imported": imported, "errors": errors, "total": len(leads)},
            "logs": [f"Imported {imported}/{len(leads)} leads"],
        }

    async def update_lead(self, lead_id: str, attributes: dict) -> dict:
        """Create or update a lead in the CRM."""
        if lead_id in self._leads:
            self._leads[lead_id].update(attributes)
            self._leads[lead_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
        else:
            self._leads[lead_id] = {
                "id": lead_id,
                **attributes,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }

        # Sync with external CRM if available
        if "hubspot" in self.crm_clients:
            try:
                await self.crm_clients["hubspot"].update_contact(lead_id, attributes)
            except Exception:
                pass

        return {
            "status": "success",
            "details": self._leads[lead_id],
            "logs": [f"Lead {lead_id} updated successfully"],
        }

    async def score_lead(self, lead_id: str) -> dict:
        """Score a specific lead using the ML scoring model."""
        lead = self._leads.get(lead_id)
        if not lead:
            return {
                "status": "error",
                "details": {"message": f"Lead {lead_id} not found"},
                "logs": [],
            }

        result = self.lead_scorer.score_lead(lead)
        # Store score on the lead
        self._leads[lead_id]["score"] = result.score
        self._leads[lead_id]["grade"] = result.grade

        return {
            "status": "success",
            "details": result.to_dict(),
            "logs": [f"Lead {lead_id} scored: {result.score} ({result.grade})"],
        }

    async def score_all_leads(self) -> dict:
        """Score all leads in the CRM."""
        results = []
        for lead_id, lead in self._leads.items():
            score_result = self.lead_scorer.score_lead(lead)
            self._leads[lead_id]["score"] = score_result.score
            self._leads[lead_id]["grade"] = score_result.grade
            results.append(score_result.to_dict())

        return {
            "status": "success",
            "details": {"scored_count": len(results), "results": results},
            "logs": [f"Scored {len(results)} leads"],
        }

    # ── Campaign management ────────────────────────────────────────────

    async def create_campaign(
        self,
        name: str,
        audience_query: Optional[dict] = None,
        content: Optional[dict] = None,
        schedule: Optional[dict] = None,
        channel: str = "email",
    ) -> dict:
        """Create and schedule a multi-channel campaign."""
        campaign_id = str(uuid.uuid4())
        campaign = {
            "id": campaign_id,
            "name": name,
            "channel": channel,
            "status": "draft",
            "audience_query": audience_query or {},
            "content": content or {},
            "schedule": schedule or {},
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._campaigns[campaign_id] = campaign

        return {
            "status": "success",
            "details": campaign,
            "logs": [f"Campaign '{name}' created with ID {campaign_id}"],
        }

    async def predict_campaign_performance(self, campaign_id: str,
                                           avg_order_value: float = 50.0) -> dict:
        """Predict performance for a campaign before launch."""
        campaign = self._campaigns.get(campaign_id)
        if not campaign:
            return {
                "status": "error",
                "details": {"message": f"Campaign {campaign_id} not found"},
                "logs": [],
            }

        # Get audience leads if available
        audience = list(self._leads.values())
        prediction = self.campaign_predictor.predict(campaign, audience, avg_order_value)

        return {
            "status": "success",
            "details": prediction.to_dict(),
            "logs": [f"Performance prediction generated for campaign {campaign_id}"],
        }

    # ── Workflow management ─────────────────────────────────────────────

    async def trigger_workflow(self, workflow_id: str, lead_id: str) -> dict:
        """Enrol a lead in a workflow and execute the first step."""
        return await self.workflow_engine.enrol_lead(workflow_id, lead_id)

    async def advance_workflow(self, workflow_id: str, lead_id: str,
                               condition_results: Optional[dict] = None) -> dict:
        """Advance a workflow to the next step."""
        return await self.workflow_engine.advance_workflow(
            workflow_id, lead_id, condition_results
        )

    # ── Journey management ──────────────────────────────────────────────

    def initialise_journey(self, lead_id: str,
                           stage: str = "awareness") -> dict:
        """Start tracking a lead's customer journey."""
        return self.journey_mapper.initialise_journey(
            lead_id, JourneyStage(stage)
        )

    def record_touchpoint(self, lead_id: str, channel: str,
                          action: str, details: Optional[dict] = None) -> dict:
        """Record a touchpoint in the customer journey."""
        return self.journey_mapper.record_touchpoint(
            lead_id, channel, action, details
        )

    def advance_journey_stage(self, lead_id: str,
                              target_stage: Optional[str] = None) -> dict:
        """Move a lead to the next journey stage."""
        target = JourneyStage(target_stage) if target_stage else None
        return self.journey_mapper.advance_stage(lead_id, target)

    def get_journey(self, lead_id: str) -> Optional[dict]:
        """Get the full journey for a lead."""
        return self.journey_mapper.get_journey(lead_id)

    def get_funnel_metrics(self) -> dict:
        """Get funnel conversion metrics."""
        return self.journey_mapper.get_funnel_metrics()

    # ── Segmentation ────────────────────────────────────────────────────

    def create_segment(self, name: str, rules: list[dict],
                       logic: str = "and", **kwargs) -> dict:
        """Create a new segment."""
        return self.segmentation_engine.create_segment(name, rules, logic, **kwargs)

    def evaluate_segments(self, lead_id: Optional[str] = None) -> dict:
        """Evaluate leads against all segments."""
        if lead_id:
            lead = self._leads.get(lead_id)
            if lead:
                matches = self.segmentation_engine.evaluate_lead(lead)
                return {"status": "success", "details": {"lead_id": lead_id, "segments": matches}}
            return {"status": "error", "details": {"message": "Lead not found"}}

        results = self.segmentation_engine.evaluate_leads_batch(list(self._leads.values()))
        return {"status": "success", "details": results}

    def auto_segment_leads(self) -> dict:
        """Auto-segment all leads by engagement tier."""
        leads = list(self._leads.values())
        return self.segmentation_engine.auto_segment_by_engagement(leads)

    # ── Compliance ──────────────────────────────────────────────────────

    async def check_compliance(self, message: str, channel: str) -> dict:
        """Check whether a message complies with regulations."""
        return self.compliance_engine.check_content_compliance(message, channel)

    def record_consent(self, lead_id: str, channel: str, **kwargs) -> dict:
        """Record consent for a lead."""
        return self.compliance_engine.record_consent(lead_id, channel, **kwargs)

    def withdraw_consent(self, lead_id: str, channel: str) -> dict:
        """Withdraw consent for a lead."""
        return self.compliance_engine.withdraw_consent(lead_id, channel)

    def handle_data_subject_request(self, lead_id: str, right: str) -> dict:
        """Handle a GDPR data subject request."""
        lead_data = self._leads.get(lead_id)
        return self.compliance_engine.handle_data_subject_request(
            lead_id, right, lead_data, self._leads
        )

    def pre_send_check(self, lead_id: str, channel: str, message: str) -> dict:
        """Run a pre-send compliance gate."""
        return self.compliance_engine.pre_send_check(lead_id, channel, message)

    # ── A/B Testing ─────────────────────────────────────────────────────

    def create_ab_test(self, campaign_id: str, name: str,
                       variants: list[dict], **kwargs) -> dict:
        """Create an A/B test for a campaign."""
        return self.ab_testing_engine.create_test(campaign_id, name, variants, **kwargs)

    def record_ab_event(self, test_id: str, variant_id: str,
                        event_type: str, **kwargs) -> dict:
        """Record an event for an A/B test variant."""
        return self.ab_testing_engine.record_event(test_id, variant_id, event_type, **kwargs)

    def analyse_ab_test(self, test_id: str) -> dict:
        """Analyse an A/B test for statistical significance."""
        return self.ab_testing_engine.analyse_test(test_id)

    # ── Accessors ───────────────────────────────────────────────────────

    def get_leads(self) -> list[dict]:
        """Return all leads in the in-memory store."""
        return list(self._leads.values())

    def get_campaigns(self) -> list[dict]:
        """Return all campaigns in the in-memory store."""
        return list(self._campaigns.values())

    def get_lead(self, lead_id: str) -> Optional[dict]:
        """Return a single lead by ID."""
        return self._leads.get(lead_id)

    def get_campaign(self, campaign_id: str) -> Optional[dict]:
        """Return a single campaign by ID."""
        return self._campaigns.get(campaign_id)
