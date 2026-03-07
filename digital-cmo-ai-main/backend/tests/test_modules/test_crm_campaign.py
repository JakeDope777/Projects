"""
Comprehensive unit tests for the CRM & Campaign Management Module.

Covers:
- Lead management (create, update, import, score)
- ML-based lead scoring
- Workflow automation (all templates, branching, events)
- Customer journey mapping
- Smart segmentation (rules, RFM, auto-segment)
- Campaign performance prediction
- Compliance (GDPR, CAN-SPAM, CASL, consent, DSR)
- A/B testing with statistical significance
"""

import pytest
from app.modules.crm_campaign import CRMCampaignModule
from app.modules.crm_campaign.lead_scoring import (
    LeadScoringModel, FeatureEngineer, ENGAGEMENT_FEATURES,
    DEMOGRAPHIC_FEATURES, BEHAVIORAL_FEATURES, ALL_FEATURES,
)
from app.modules.crm_campaign.workflow_automation import (
    WorkflowEngine, WORKFLOW_TEMPLATES, WorkflowStatus, ActionType, TriggerType,
)
from app.modules.crm_campaign.journey_mapping import (
    JourneyMapper, JourneyStage, STAGE_ORDER, STAGE_INDEX,
)
from app.modules.crm_campaign.segmentation import (
    SegmentationEngine, SegmentRule, Operator, RFMAnalyser,
)
from app.modules.crm_campaign.campaign_predictor import (
    CampaignPredictor, CHANNEL_BENCHMARKS,
)
from app.modules.crm_campaign.compliance import (
    ComplianceEngine, ConsentType, ConsentChannel, DataSubjectRight,
)
from app.modules.crm_campaign.ab_testing import (
    ABTestingEngine, StatisticalCalculator, TestStatus, TestMetric,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def module():
    return CRMCampaignModule()


@pytest.fixture
def sample_lead():
    return {
        "id": "lead-001",
        "name": "Jane Doe",
        "email": "jane@example.com",
        "status": "active",
        "engagement": {
            "email_opens": 15,
            "email_clicks": 8,
            "website_visits": 25,
            "page_views": 80,
            "content_downloads": 3,
            "webinar_attendance": 1,
            "social_interactions": 5,
            "form_submissions": 2,
            "demo_requests": 1,
            "support_tickets": 0,
        },
        "demographics": {
            "job_title": "Marketing Director",
            "company_size": "201-1000",
            "industry": "Technology",
            "country": "us",
            "budget": "25001-100000",
        },
        "behavior": {
            "last_activity_date": "2026-03-01T10:00:00+00:00",
            "session_duration_avg": 300,
            "pages_per_session": 8,
            "return_visit_ratio": 0.6,
            "pricing_page_visits": 5,
            "competitor_comparison_views": 2,
            "trial_signup": True,
            "cart_abandonment_count": 0,
        },
    }


@pytest.fixture
def sample_lead_cold():
    return {
        "id": "lead-cold",
        "name": "Cold Lead",
        "email": "cold@example.com",
        "status": "inactive",
        "engagement": {
            "email_opens": 0,
            "email_clicks": 0,
            "website_visits": 1,
            "page_views": 2,
        },
        "demographics": {
            "job_title": "Intern",
            "company_size": "1-10",
            "industry": "Other",
            "country": "unknown",
        },
        "behavior": {
            "days_since_last_activity": 120,
            "session_duration_avg": 10,
            "pages_per_session": 1,
            "return_visit_ratio": 0,
            "pricing_page_visits": 0,
        },
    }


@pytest.fixture
def multiple_leads(sample_lead, sample_lead_cold):
    return [
        sample_lead,
        sample_lead_cold,
        {
            "id": "lead-mid",
            "name": "Mid Lead",
            "score": 45,
            "engagement": {"email_opens": 5, "email_clicks": 2, "website_visits": 10,
                           "form_submissions": 1, "demo_requests": 0},
            "demographics": {"job_title": "Manager", "company_size": "51-200",
                             "industry": "Marketing", "country": "uk"},
            "behavior": {"days_since_last_activity": 10, "session_duration_avg": 120,
                         "pages_per_session": 4, "return_visit_ratio": 0.3,
                         "pricing_page_visits": 1},
        },
    ]


# ===========================================================================
# Test CRMCampaignModule (integration)
# ===========================================================================

class TestCRMCampaignModule:
    """Tests for the main CRM module orchestrator."""

    @pytest.mark.asyncio
    async def test_update_lead_create(self, module):
        result = await module.update_lead("lead-001", {"name": "Jane Doe", "email": "jane@example.com"})
        assert result["status"] == "success"
        assert result["details"]["id"] == "lead-001"

    @pytest.mark.asyncio
    async def test_update_lead_update(self, module):
        await module.update_lead("lead-002", {"name": "John"})
        result = await module.update_lead("lead-002", {"name": "John Smith"})
        assert result["status"] == "success"
        assert result["details"]["name"] == "John Smith"

    @pytest.mark.asyncio
    async def test_import_leads(self, module):
        leads = [
            {"id": "imp-1", "name": "Lead A"},
            {"id": "imp-2", "name": "Lead B"},
            {"name": "Lead C"},  # no id – should auto-generate
        ]
        result = await module.import_leads(leads)
        assert result["status"] == "success"
        assert result["details"]["imported"] == 3
        assert len(module.get_leads()) == 3

    @pytest.mark.asyncio
    async def test_create_campaign(self, module):
        result = await module.create_campaign(
            name="Spring Sale",
            channel="email",
            content={"subject": "Spring Sale!", "body": "Don't miss out"},
        )
        assert result["status"] == "success"
        assert "id" in result["details"]
        assert result["details"]["name"] == "Spring Sale"

    @pytest.mark.asyncio
    async def test_score_lead(self, module, sample_lead):
        await module.update_lead("lead-001", sample_lead)
        result = await module.score_lead("lead-001")
        assert result["status"] == "success"
        assert "score" in result["details"]
        assert result["details"]["score"] > 0

    @pytest.mark.asyncio
    async def test_score_lead_not_found(self, module):
        result = await module.score_lead("nonexistent")
        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_score_all_leads(self, module, sample_lead, sample_lead_cold):
        await module.update_lead("lead-001", sample_lead)
        await module.update_lead("lead-cold", sample_lead_cold)
        result = await module.score_all_leads()
        assert result["status"] == "success"
        assert result["details"]["scored_count"] == 2

    @pytest.mark.asyncio
    async def test_trigger_workflow_welcome(self, module):
        result = await module.trigger_workflow("welcome_series", "lead-100")
        assert result["status"] == "success"
        assert result["details"]["workflow"] == "welcome_series"

    @pytest.mark.asyncio
    async def test_trigger_workflow_unknown(self, module):
        result = await module.trigger_workflow("nonexistent_workflow", "lead-300")
        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_handle_lead(self, module):
        result = await module.handle("Tell me about lead management", {})
        assert "response" in result

    @pytest.mark.asyncio
    async def test_handle_scoring(self, module):
        result = await module.handle("How does lead scoring work?", {})
        assert "scoring" in result["response"].lower()

    @pytest.mark.asyncio
    async def test_handle_journey(self, module):
        result = await module.handle("Show me the customer journey", {})
        assert "journey" in result["response"].lower()

    @pytest.mark.asyncio
    async def test_handle_segment(self, module):
        result = await module.handle("Create a segment", {})
        assert "segment" in result["response"].lower()

    @pytest.mark.asyncio
    async def test_handle_ab_test(self, module):
        result = await module.handle("Set up an A/B test", {})
        assert "A/B" in result["response"]

    @pytest.mark.asyncio
    async def test_handle_compliance(self, module):
        result = await module.handle("Check GDPR compliance", {})
        assert "compliance" in result["response"].lower() or "Compliance" in result["response"]

    @pytest.mark.asyncio
    async def test_handle_default(self, module):
        result = await module.handle("Hello", {})
        assert "response" in result

    def test_get_leads_empty(self, module):
        assert module.get_leads() == []

    def test_get_campaigns_empty(self, module):
        assert module.get_campaigns() == []

    @pytest.mark.asyncio
    async def test_predict_campaign_performance(self, module):
        result = await module.create_campaign(
            name="Test Campaign", channel="email",
            content={"subject": "Test", "body": "Click here to learn more"},
        )
        campaign_id = result["details"]["id"]
        prediction = await module.predict_campaign_performance(campaign_id)
        assert prediction["status"] == "success"
        assert "predicted_metrics" in prediction["details"]

    @pytest.mark.asyncio
    async def test_predict_campaign_not_found(self, module):
        result = await module.predict_campaign_performance("nonexistent")
        assert result["status"] == "error"


# ===========================================================================
# Test Lead Scoring
# ===========================================================================

class TestLeadScoring:
    """Tests for the ML-based lead scoring engine."""

    def test_feature_extraction(self, sample_lead):
        features = FeatureEngineer.extract_features(sample_lead)
        assert "email_opens" in features
        assert features["email_opens"] == 15.0
        assert features["job_title_level"] == 4.0  # Director
        assert features["industry_match"] == 1.0   # Technology
        assert features["geo_tier"] == 2.0          # US
        assert features["trial_signup"] == 1.0

    def test_feature_extraction_empty_lead(self):
        features = FeatureEngineer.extract_features({})
        assert len(features) == len(ALL_FEATURES)
        assert features["email_opens"] == 0.0

    def test_score_lead_high_engagement(self, sample_lead):
        scorer = LeadScoringModel()
        result = scorer.score_lead(sample_lead)
        assert result.score > 30
        assert result.grade in ("A+", "A", "B+", "B", "C+", "C")
        assert 0 < result.conversion_probability < 1
        assert len(result.top_factors) > 0
        assert result.recommended_action != ""

    def test_score_lead_cold(self, sample_lead_cold):
        scorer = LeadScoringModel()
        result = scorer.score_lead(sample_lead_cold)
        assert result.score < 30
        assert result.grade in ("D", "F", "C")

    def test_score_leads_batch(self, sample_lead, sample_lead_cold):
        scorer = LeadScoringModel()
        results = scorer.score_leads_batch([sample_lead, sample_lead_cold])
        assert len(results) == 2
        assert results[0].score > results[1].score

    def test_score_components(self, sample_lead):
        scorer = LeadScoringModel()
        result = scorer.score_lead(sample_lead)
        components = result.score_components
        assert "engagement" in components
        assert "demographic" in components
        assert "behavioral" in components
        assert "recency_decay" in components

    def test_training_insufficient_data(self):
        scorer = LeadScoringModel()
        scorer.add_training_sample({"email_opens": 10}, True)
        metrics = scorer.train()
        assert metrics.sample_count == 0  # Not enough data

    def test_training_with_data(self, sample_lead, sample_lead_cold):
        scorer = LeadScoringModel()
        # Add enough training samples
        for i in range(10):
            features = FeatureEngineer.extract_features(sample_lead)
            scorer.add_training_sample(features, True)
        for i in range(10):
            features = FeatureEngineer.extract_features(sample_lead_cold)
            scorer.add_training_sample(features, False)

        metrics = scorer.train()
        assert metrics.sample_count == 20
        assert metrics.accuracy > 0
        assert metrics.trained_at is not None

    def test_model_metrics(self):
        scorer = LeadScoringModel()
        metrics = scorer.get_model_metrics()
        assert "is_trained" in metrics
        assert metrics["is_trained"] is False

    def test_score_to_dict(self, sample_lead):
        scorer = LeadScoringModel()
        result = scorer.score_lead(sample_lead)
        d = result.to_dict()
        assert "lead_id" in d
        assert "score" in d
        assert "grade" in d
        assert "conversion_probability" in d

    def test_grade_thresholds(self):
        scorer = LeadScoringModel()
        assert scorer._score_to_grade(95) == "A+"
        assert scorer._score_to_grade(85) == "A"
        assert scorer._score_to_grade(75) == "B+"
        assert scorer._score_to_grade(65) == "B"
        assert scorer._score_to_grade(55) == "C+"
        assert scorer._score_to_grade(45) == "C"
        assert scorer._score_to_grade(35) == "D"
        assert scorer._score_to_grade(10) == "F"


# ===========================================================================
# Test Workflow Automation
# ===========================================================================

class TestWorkflowAutomation:
    """Tests for the workflow automation engine."""

    def test_all_templates_exist(self):
        expected = [
            "welcome_series", "re_engagement", "lead_nurture",
            "onboarding_product", "upsell_sequence", "win_back",
            "cart_abandonment", "trial_expiry", "post_purchase",
            "referral_programme", "nps_feedback", "event_followup",
        ]
        for wf_id in expected:
            assert wf_id in WORKFLOW_TEMPLATES, f"Missing template: {wf_id}"

    def test_template_structure(self):
        for wf_id, template in WORKFLOW_TEMPLATES.items():
            assert "name" in template, f"{wf_id} missing name"
            assert "steps" in template, f"{wf_id} missing steps"
            assert len(template["steps"]) > 0, f"{wf_id} has no steps"

    @pytest.mark.asyncio
    async def test_enrol_lead(self):
        engine = WorkflowEngine()
        result = await engine.enrol_lead("welcome_series", "lead-1")
        assert result["status"] == "success"
        assert result["details"]["workflow"] == "welcome_series"

    @pytest.mark.asyncio
    async def test_enrol_lead_already_enrolled(self):
        engine = WorkflowEngine()
        await engine.enrol_lead("welcome_series", "lead-1")
        result = await engine.enrol_lead("welcome_series", "lead-1")
        assert result["status"] == "already_enrolled"

    @pytest.mark.asyncio
    async def test_advance_workflow(self):
        engine = WorkflowEngine()
        await engine.enrol_lead("welcome_series", "lead-1")
        result = await engine.advance_workflow("welcome_series", "lead-1")
        assert result["status"] in ("success", "completed")

    @pytest.mark.asyncio
    async def test_advance_unknown_workflow(self):
        engine = WorkflowEngine()
        result = await engine.advance_workflow("nonexistent", "lead-1")
        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_advance_not_enrolled(self):
        engine = WorkflowEngine()
        result = await engine.advance_workflow("welcome_series", "lead-999")
        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_workflow_completion(self):
        engine = WorkflowEngine()
        await engine.enrol_lead("post_purchase", "lead-1")
        # Advance through all steps
        for _ in range(20):
            result = await engine.advance_workflow("post_purchase", "lead-1")
            if result["status"] == "completed":
                break
        assert result["status"] == "completed"

    def test_pause_resume_cancel(self):
        engine = WorkflowEngine()
        # Need to enrol first via sync-compatible method
        import asyncio
        asyncio.get_event_loop().run_until_complete(
            engine.enrol_lead("welcome_series", "lead-1")
        )
        result = engine.pause_workflow("welcome_series", "lead-1")
        assert result["status"] == "paused"

        result = engine.resume_workflow("welcome_series", "lead-1")
        assert result["status"] == "resumed"

        result = engine.cancel_workflow("welcome_series", "lead-1")
        assert result["status"] == "cancelled"

    def test_get_available_workflows(self):
        engine = WorkflowEngine()
        workflows = engine.get_available_workflows()
        assert len(workflows) >= 12
        for wf_id, info in workflows.items():
            assert "name" in info
            assert "step_count" in info

    def test_get_workflow_categories(self):
        engine = WorkflowEngine()
        categories = engine.get_workflow_categories()
        assert len(categories) > 0
        assert "onboarding" in categories

    @pytest.mark.asyncio
    async def test_event_trigger(self):
        engine = WorkflowEngine()
        engine.register_event_trigger("lead_created", "welcome_series")
        results = await engine.fire_event("lead_created", "lead-new")
        assert len(results) == 1
        assert results[0]["status"] == "success"

    @pytest.mark.asyncio
    async def test_get_lead_workflows(self):
        engine = WorkflowEngine()
        await engine.enrol_lead("welcome_series", "lead-1")
        await engine.enrol_lead("lead_nurture", "lead-1")
        workflows = engine.get_lead_workflows("lead-1")
        assert len(workflows) == 2

    @pytest.mark.asyncio
    async def test_workflow_stats(self):
        engine = WorkflowEngine()
        await engine.enrol_lead("welcome_series", "lead-1")
        await engine.enrol_lead("welcome_series", "lead-2")
        stats = engine.get_workflow_stats("welcome_series")
        assert stats["total_enrolled"] == 2
        assert stats["active"] >= 0

    @pytest.mark.asyncio
    async def test_execution_log(self):
        engine = WorkflowEngine()
        await engine.enrol_lead("welcome_series", "lead-1")
        log = engine.get_execution_log(workflow_id="welcome_series")
        assert len(log) > 0


# ===========================================================================
# Test Customer Journey Mapping
# ===========================================================================

class TestJourneyMapping:
    """Tests for the customer journey mapping engine."""

    def test_initialise_journey(self):
        mapper = JourneyMapper()
        result = mapper.initialise_journey("lead-1")
        assert result["status"] == "success"
        assert result["details"]["current_stage"] == "awareness"

    def test_initialise_journey_custom_stage(self):
        mapper = JourneyMapper()
        result = mapper.initialise_journey("lead-1", JourneyStage.CONSIDERATION)
        assert result["details"]["current_stage"] == "consideration"

    def test_record_touchpoint(self):
        mapper = JourneyMapper()
        mapper.initialise_journey("lead-1")
        result = mapper.record_touchpoint("lead-1", "email", "opened", {"campaign": "spring"})
        assert result["status"] == "success"
        assert result["details"]["channel"] == "email"

    def test_record_touchpoint_auto_init(self):
        mapper = JourneyMapper()
        result = mapper.record_touchpoint("lead-new", "social", "liked")
        assert result["status"] == "success"

    def test_advance_stage(self):
        mapper = JourneyMapper()
        mapper.initialise_journey("lead-1")
        result = mapper.advance_stage("lead-1")
        assert result["status"] == "success"
        assert result["details"]["current_stage"] == "interest"

    def test_advance_stage_to_specific(self):
        mapper = JourneyMapper()
        mapper.initialise_journey("lead-1")
        result = mapper.advance_stage("lead-1", JourneyStage.INTENT)
        assert result["details"]["current_stage"] == "intent"

    def test_advance_stage_no_journey(self):
        mapper = JourneyMapper()
        result = mapper.advance_stage("nonexistent")
        assert result["status"] == "error"

    def test_advance_to_final_stage(self):
        mapper = JourneyMapper()
        mapper.initialise_journey("lead-1", JourneyStage.ADVOCACY)
        result = mapper.advance_stage("lead-1")
        assert result["status"] == "already_at_final_stage"

    def test_get_journey(self):
        mapper = JourneyMapper()
        mapper.initialise_journey("lead-1")
        mapper.record_touchpoint("lead-1", "email", "opened")
        journey = mapper.get_journey("lead-1")
        assert journey is not None
        assert journey["touchpoint_count"] == 1
        assert "current_stage_config" in journey

    def test_get_journey_not_found(self):
        mapper = JourneyMapper()
        assert mapper.get_journey("nonexistent") is None

    def test_funnel_metrics(self):
        mapper = JourneyMapper()
        mapper.initialise_journey("lead-1")
        mapper.initialise_journey("lead-2")
        mapper.advance_stage("lead-1")  # Move to interest
        metrics = mapper.get_funnel_metrics()
        assert metrics["total_journeys"] == 2
        assert "current_stage_distribution" in metrics
        assert "stage_conversion_rates" in metrics

    def test_bottlenecks(self):
        mapper = JourneyMapper()
        for i in range(10):
            mapper.initialise_journey(f"lead-{i}")
        # Only advance 2 leads
        mapper.advance_stage("lead-0")
        mapper.advance_stage("lead-1")
        bottlenecks = mapper.get_bottlenecks()
        assert isinstance(bottlenecks, list)

    def test_get_leads_at_stage(self):
        mapper = JourneyMapper()
        mapper.initialise_journey("lead-1")
        mapper.initialise_journey("lead-2")
        mapper.advance_stage("lead-1")
        awareness_leads = mapper.get_leads_at_stage(JourneyStage.AWARENESS)
        assert "lead-2" in awareness_leads
        interest_leads = mapper.get_leads_at_stage(JourneyStage.INTEREST)
        assert "lead-1" in interest_leads

    def test_channel_attribution(self):
        mapper = JourneyMapper()
        mapper.initialise_journey("lead-1")
        mapper.record_touchpoint("lead-1", "email", "opened")
        mapper.record_touchpoint("lead-1", "social", "liked")
        mapper.record_touchpoint("lead-1", "email", "clicked")
        attribution = mapper.get_channel_attribution()
        assert "email" in attribution
        assert attribution["email"]["total_touchpoints"] == 2

    def test_all_stages(self):
        mapper = JourneyMapper()
        stages = mapper.get_all_stages()
        assert len(stages) == len(STAGE_ORDER)

    def test_stage_order(self):
        assert STAGE_INDEX[JourneyStage.AWARENESS] == 0
        assert STAGE_INDEX[JourneyStage.ADVOCACY] == len(STAGE_ORDER) - 1


# ===========================================================================
# Test Smart Segmentation
# ===========================================================================

class TestSegmentation:
    """Tests for the smart segmentation engine."""

    def test_create_segment(self):
        engine = SegmentationEngine()
        result = engine.create_segment(
            name="High Value",
            rules=[{"field": "score", "operator": "greater_or_equal", "value": 70}],
        )
        assert result["status"] == "success"
        assert result["details"]["name"] == "High Value"

    def test_create_from_template(self):
        engine = SegmentationEngine()
        result = engine.create_from_template("high_value_leads")
        assert result["status"] == "success"
        assert "High-Value" in result["details"]["name"]

    def test_create_from_unknown_template(self):
        engine = SegmentationEngine()
        result = engine.create_from_template("nonexistent")
        assert result["status"] == "error"

    def test_evaluate_lead_match(self):
        engine = SegmentationEngine()
        engine.create_segment(
            name="High Score",
            rules=[{"field": "score", "operator": "greater_or_equal", "value": 70}],
        )
        lead = {"id": "lead-1", "score": 85}
        matches = engine.evaluate_lead(lead)
        assert len(matches) == 1
        assert matches[0]["segment_name"] == "High Score"

    def test_evaluate_lead_no_match(self):
        engine = SegmentationEngine()
        engine.create_segment(
            name="High Score",
            rules=[{"field": "score", "operator": "greater_or_equal", "value": 70}],
        )
        lead = {"id": "lead-1", "score": 30}
        matches = engine.evaluate_lead(lead)
        assert len(matches) == 0

    def test_evaluate_lead_multiple_segments(self):
        engine = SegmentationEngine()
        engine.create_segment(
            name="High Score",
            rules=[{"field": "score", "operator": "greater_or_equal", "value": 50}],
        )
        engine.create_segment(
            name="US Leads",
            rules=[{"field": "demographics.country", "operator": "equals", "value": "us"}],
        )
        lead = {"id": "lead-1", "score": 80, "demographics": {"country": "us"}}
        matches = engine.evaluate_lead(lead)
        assert len(matches) == 2

    def test_segment_rule_operators(self):
        # Test various operators
        rule_eq = SegmentRule(field="status", operator=Operator.EQUALS, value="active")
        assert rule_eq.evaluate({"status": "active"}) is True
        assert rule_eq.evaluate({"status": "inactive"}) is False

        rule_ne = SegmentRule(field="status", operator=Operator.NOT_EQUALS, value="churned")
        assert rule_ne.evaluate({"status": "active"}) is True

        rule_gt = SegmentRule(field="score", operator=Operator.GREATER_THAN, value=50)
        assert rule_gt.evaluate({"score": 60}) is True
        assert rule_gt.evaluate({"score": 40}) is False

        rule_lt = SegmentRule(field="score", operator=Operator.LESS_THAN, value=50)
        assert rule_lt.evaluate({"score": 30}) is True

        rule_contains = SegmentRule(field="name", operator=Operator.CONTAINS, value="jane")
        assert rule_contains.evaluate({"name": "Jane Doe"}) is True

        rule_in = SegmentRule(field="country", operator=Operator.IN, value=["us", "uk"])
        assert rule_in.evaluate({"country": "us"}) is True
        assert rule_in.evaluate({"country": "de"}) is False

        rule_between = SegmentRule(field="score", operator=Operator.BETWEEN, value=30, value_secondary=70)
        assert rule_between.evaluate({"score": 50}) is True
        assert rule_between.evaluate({"score": 80}) is False

        rule_exists = SegmentRule(field="email", operator=Operator.EXISTS)
        assert rule_exists.evaluate({"email": "test@test.com"}) is True
        assert rule_exists.evaluate({"name": "test"}) is False

    def test_nested_field_access(self):
        rule = SegmentRule(field="demographics.country", operator=Operator.EQUALS, value="us")
        assert rule.evaluate({"demographics": {"country": "us"}}) is True
        assert rule.evaluate({"demographics": {"country": "uk"}}) is False

    def test_or_logic(self):
        engine = SegmentationEngine()
        engine.create_segment(
            name="US or High Score",
            rules=[
                {"field": "demographics.country", "operator": "equals", "value": "us"},
                {"field": "score", "operator": "greater_or_equal", "value": 80},
            ],
            logic="or",
        )
        lead_us = {"id": "l1", "demographics": {"country": "us"}, "score": 30}
        lead_high = {"id": "l2", "demographics": {"country": "de"}, "score": 90}
        assert len(engine.evaluate_lead(lead_us)) == 1
        assert len(engine.evaluate_lead(lead_high)) == 1

    def test_auto_segment_by_engagement(self, multiple_leads):
        engine = SegmentationEngine()
        # Add scores to leads
        for lead in multiple_leads:
            lead.setdefault("score", 30)
        multiple_leads[0]["score"] = 80
        multiple_leads[1]["score"] = 5
        multiple_leads[2]["score"] = 45

        result = engine.auto_segment_by_engagement(multiple_leads)
        assert "tiers" in result
        assert result["total_leads"] == 3

    def test_rfm_analysis(self, multiple_leads):
        results = RFMAnalyser.analyse(multiple_leads)
        assert len(results) == 3
        for r in results:
            assert "rfm_score" in r
            assert "segment" in r
            assert 1 <= r["recency_score"] <= 5

    def test_rfm_empty(self):
        assert RFMAnalyser.analyse([]) == []

    def test_segment_stats(self):
        engine = SegmentationEngine()
        engine.create_segment("Seg A", [{"field": "score", "operator": "greater_than", "value": 50}])
        engine.evaluate_lead({"id": "l1", "score": 60})
        stats = engine.get_segment_stats()
        assert stats["total_segments"] == 1

    def test_delete_segment(self):
        engine = SegmentationEngine()
        result = engine.create_segment("Temp", [{"field": "score", "operator": "equals", "value": 0}])
        seg_id = result["details"]["id"]
        del_result = engine.delete_segment(seg_id)
        assert del_result["status"] == "success"
        assert engine.get_segment(seg_id) is None

    def test_available_templates(self):
        engine = SegmentationEngine()
        templates = engine.get_available_templates()
        assert len(templates) >= 10
        assert "high_value_leads" in templates


# ===========================================================================
# Test Campaign Performance Predictor
# ===========================================================================

class TestCampaignPredictor:
    """Tests for the campaign performance prediction engine."""

    def test_predict_email_campaign(self):
        predictor = CampaignPredictor()
        campaign = {
            "id": "camp-1",
            "channel": "email",
            "content": {
                "subject": "Limited time offer – save 20%!",
                "body": "Click here to learn more about our discount. Trusted by 1000+ customers.",
            },
            "schedule": {"send_hour": 10, "send_day": 1},
        }
        result = predictor.predict(campaign, avg_order_value=100)
        assert result.predicted_open_rate > 0
        assert result.predicted_click_rate > 0
        assert result.predicted_conversion_rate > 0
        assert result.audience_size == 1000  # default
        assert len(result.recommendations) >= 0

    def test_predict_with_audience(self, multiple_leads):
        predictor = CampaignPredictor()
        for lead in multiple_leads:
            lead["score"] = 60
        campaign = {"id": "camp-2", "channel": "email", "content": {}, "schedule": {}}
        result = predictor.predict(campaign, audience=multiple_leads)
        assert result.audience_size == 3

    def test_predict_social_campaign(self):
        predictor = CampaignPredictor()
        campaign = {"id": "camp-3", "channel": "social", "content": {"body": "Check this out!"}}
        result = predictor.predict(campaign)
        assert result.channel == "social"

    def test_predict_ads_campaign(self):
        predictor = CampaignPredictor()
        campaign = {"id": "camp-4", "channel": "ads", "content": {"body": "Sign up now"}}
        result = predictor.predict(campaign)
        assert result.channel == "ads"

    def test_prediction_to_dict(self):
        predictor = CampaignPredictor()
        campaign = {"id": "camp-5", "channel": "email", "content": {}}
        result = predictor.predict(campaign)
        d = result.to_dict()
        assert "predicted_metrics" in d
        assert "confidence_intervals" in d
        assert "roi_projection" in d
        assert "quality_scores" in d
        assert "recommendations" in d

    def test_content_quality_personalisation(self):
        predictor = CampaignPredictor()
        campaign_personal = {
            "id": "c1", "channel": "email",
            "content": {"subject": "Hi {{first_name}}", "body": "Click here to sign up"},
        }
        campaign_generic = {
            "id": "c2", "channel": "email",
            "content": {"subject": "Newsletter", "body": "Read more"},
        }
        r1 = predictor.predict(campaign_personal)
        r2 = predictor.predict(campaign_generic)
        assert r1.content_quality_score >= r2.content_quality_score

    def test_record_actual_performance(self):
        predictor = CampaignPredictor()
        predictor.record_actual_performance("camp-1", "email", {"open_rate": 0.25})
        assert len(predictor._historical_campaigns) == 1

    def test_channel_benchmarks(self):
        predictor = CampaignPredictor()
        benchmarks = predictor.get_channel_benchmarks()
        assert "email" in benchmarks
        assert "social" in benchmarks
        email_bench = predictor.get_channel_benchmarks("email")
        assert "open_rate" in email_bench

    def test_optimal_send_time(self):
        predictor = CampaignPredictor()
        campaign = {"id": "c1", "channel": "email", "content": {}, "schedule": {}}
        result = predictor.predict(campaign)
        assert result.optimal_send_time != ""


# ===========================================================================
# Test Compliance Engine
# ===========================================================================

class TestCompliance:
    """Tests for the compliance management engine."""

    def test_record_consent(self):
        engine = ComplianceEngine()
        result = engine.record_consent("lead-1", "email", source="web_form")
        assert result["status"] == "success"
        assert result["details"]["granted"] is True

    def test_check_consent_valid(self):
        engine = ComplianceEngine()
        engine.record_consent("lead-1", "email")
        result = engine.check_consent("lead-1", "email")
        assert result["has_consent"] is True

    def test_check_consent_no_consent(self):
        engine = ComplianceEngine()
        result = engine.check_consent("lead-1", "email")
        assert result["has_consent"] is False

    def test_withdraw_consent(self):
        engine = ComplianceEngine()
        engine.record_consent("lead-1", "email")
        result = engine.withdraw_consent("lead-1", "email")
        assert result["status"] == "success"
        # Consent should now be invalid
        check = engine.check_consent("lead-1", "email")
        assert check["has_consent"] is False

    def test_withdraw_consent_not_found(self):
        engine = ComplianceEngine()
        result = engine.withdraw_consent("lead-1", "email")
        assert result["status"] == "not_found"

    def test_consent_status(self):
        engine = ComplianceEngine()
        engine.record_consent("lead-1", "email")
        engine.record_consent("lead-1", "sms")
        status = engine.get_consent_status("lead-1")
        assert "email" in status["channels"]
        assert "sms" in status["channels"]

    def test_compliance_check_email_pass(self):
        engine = ComplianceEngine()
        message = (
            "Check out our offer! unsubscribe link sender address company name "
            "physical address privacy policy link sender identity purpose of processing "
            "contact information"
        )
        result = engine.check_content_compliance(message, "email")
        assert result["details"]["is_compliant"] is True

    def test_compliance_check_email_fail(self):
        engine = ComplianceEngine()
        result = engine.check_content_compliance("Buy now!", "email")
        assert result["status"] == "non_compliant"
        assert len(result["details"]["issues"]) > 0

    def test_compliance_check_prohibited_pattern(self):
        engine = ComplianceEngine()
        result = engine.check_content_compliance("Guaranteed results!", "email")
        assert result["status"] == "non_compliant"

    def test_compliance_check_social(self):
        engine = ComplianceEngine()
        result = engine.check_content_compliance(
            "Great content! unsubscribe privacy policy link contact information", "social"
        )
        assert result["details"]["is_compliant"] is True

    def test_gdpr_access_request(self):
        engine = ComplianceEngine()
        lead_data = {"id": "lead-1", "name": "Jane", "email": "jane@test.com"}
        result = engine.handle_data_subject_request("lead-1", "access", lead_data)
        assert result["status"] == "success"
        assert "lead_data" in result["details"]["data"]

    def test_gdpr_export_request(self):
        engine = ComplianceEngine()
        lead_data = {"id": "lead-1", "name": "Jane"}
        result = engine.handle_data_subject_request("lead-1", "export", lead_data)
        assert result["status"] == "success"
        assert "lead_profile" in result["details"]["data"]

    def test_gdpr_erasure_request(self):
        engine = ComplianceEngine()
        leads_store = {"lead-1": {"id": "lead-1", "name": "Jane"}}
        result = engine.handle_data_subject_request("lead-1", "erasure", leads_store=leads_store)
        assert result["status"] == "success"
        assert "lead-1" not in leads_store
        assert engine.is_suppressed("lead-1")

    def test_gdpr_restriction_request(self):
        engine = ComplianceEngine()
        result = engine.handle_data_subject_request("lead-1", "restriction")
        assert result["status"] == "success"
        assert engine.is_suppressed("lead-1")

    def test_gdpr_objection_request(self):
        engine = ComplianceEngine()
        result = engine.handle_data_subject_request("lead-1", "objection")
        assert result["status"] == "success"
        assert engine.is_suppressed("lead-1")

    def test_gdpr_portability_request(self):
        engine = ComplianceEngine()
        lead_data = {"id": "lead-1", "name": "Jane"}
        result = engine.handle_data_subject_request("lead-1", "portability", lead_data)
        assert result["status"] == "success"
        assert result["details"]["data"]["format"] == "json"

    def test_suppression_list(self):
        engine = ComplianceEngine()
        engine.add_to_suppression("lead-1", reason="opt-out")
        assert engine.is_suppressed("lead-1")
        assert "lead-1" in engine.get_suppression_list()

        engine.remove_from_suppression("lead-1")
        assert not engine.is_suppressed("lead-1")

    def test_pre_send_check_blocked(self):
        engine = ComplianceEngine()
        engine.add_to_suppression("lead-1")
        result = engine.pre_send_check("lead-1", "email", "Hello!")
        assert result["can_send"] is False
        assert any("suppression" in b.lower() for b in result["blocks"])

    def test_pre_send_check_no_consent(self):
        engine = ComplianceEngine()
        result = engine.pre_send_check("lead-1", "email", "Hello!")
        assert result["can_send"] is False

    def test_pre_send_check_pass(self):
        engine = ComplianceEngine()
        engine.record_consent("lead-1", "email")
        message = (
            "Hello! unsubscribe link sender address company name "
            "physical address privacy policy link sender identity "
            "purpose of processing contact information"
        )
        result = engine.pre_send_check("lead-1", "email", message)
        assert result["can_send"] is True

    def test_data_retention(self):
        engine = ComplianceEngine()
        engine.set_retention_policy(365)
        leads = {
            "lead-old": {"created_at": "2020-01-01T00:00:00+00:00"},
            "lead-new": {"created_at": "2026-03-01T00:00:00+00:00"},
        }
        result = engine.check_retention_compliance(leads)
        assert result["expired_leads_count"] >= 1

    def test_breach_recording(self):
        engine = ComplianceEngine()
        breach = engine.record_breach("Test breach", ["lead-1", "lead-2"], "high")
        assert breach["severity"] == "high"
        assert breach["affected_lead_count"] == 2
        assert len(engine.get_breach_log()) == 1

    def test_audit_log(self):
        engine = ComplianceEngine()
        engine.record_consent("lead-1", "email")
        engine.withdraw_consent("lead-1", "email")
        log = engine.get_audit_log(lead_id="lead-1")
        assert len(log) >= 2

    def test_dsr_requests(self):
        engine = ComplianceEngine()
        engine.handle_data_subject_request("lead-1", "access")
        engine.handle_data_subject_request("lead-2", "erasure")
        requests = engine.get_dsr_requests()
        assert len(requests) == 2


# ===========================================================================
# Test A/B Testing
# ===========================================================================

class TestABTesting:
    """Tests for the A/B testing engine with statistical significance."""

    def test_create_test(self):
        engine = ABTestingEngine()
        result = engine.create_test(
            campaign_id="camp-1",
            name="Subject Line Test",
            variants=[
                {"name": "Control", "content": {"subject": "Hello"}, "is_control": True},
                {"name": "Treatment", "content": {"subject": "Hi there!"}},
            ],
        )
        assert result["status"] == "success"
        assert len(result["details"]["variants"]) == 2

    def test_create_test_auto_control(self):
        engine = ABTestingEngine()
        result = engine.create_test(
            campaign_id="camp-1",
            name="Auto Control Test",
            variants=[
                {"name": "A", "content": {}},
                {"name": "B", "content": {}},
            ],
        )
        # First variant should be auto-assigned as control
        assert result["details"]["variants"][0]["is_control"] is True

    def test_start_test(self):
        engine = ABTestingEngine()
        result = engine.create_test("camp-1", "Test", [
            {"name": "A", "content": {}, "is_control": True},
            {"name": "B", "content": {}},
        ])
        test_id = result["details"]["id"]
        start_result = engine.start_test(test_id)
        assert start_result["status"] == "success"

    def test_start_test_not_found(self):
        engine = ABTestingEngine()
        result = engine.start_test("nonexistent")
        assert result["status"] == "error"

    def test_record_event(self):
        engine = ABTestingEngine()
        result = engine.create_test("camp-1", "Test", [
            {"name": "A", "content": {}, "is_control": True},
            {"name": "B", "content": {}},
        ])
        test_id = result["details"]["id"]
        variant_a_id = result["details"]["variants"][0]["id"]
        engine.start_test(test_id)

        event_result = engine.record_event(test_id, variant_a_id, "send", count=100)
        assert event_result["status"] == "success"

    def test_analyse_test_no_data(self):
        engine = ABTestingEngine()
        result = engine.create_test("camp-1", "Test", [
            {"name": "A", "content": {}, "is_control": True},
            {"name": "B", "content": {}},
        ])
        test_id = result["details"]["id"]
        analysis = engine.analyse_test(test_id)
        assert analysis["status"] == "success"
        assert analysis["details"]["is_conclusive"] is False

    def test_analyse_test_with_data(self):
        engine = ABTestingEngine()
        result = engine.create_test("camp-1", "CTR Test", [
            {"name": "Control", "content": {}, "is_control": True},
            {"name": "Treatment", "content": {}},
        ])
        test_id = result["details"]["id"]
        control_id = result["details"]["variants"][0]["id"]
        treatment_id = result["details"]["variants"][1]["id"]
        engine.start_test(test_id)

        # Simulate data: control has 2% CTR, treatment has 4% CTR
        engine.record_event(test_id, control_id, "send", count=1000)
        engine.record_event(test_id, control_id, "click", count=20)
        engine.record_event(test_id, treatment_id, "send", count=1000)
        engine.record_event(test_id, treatment_id, "click", count=40)

        analysis = engine.analyse_test(test_id)
        assert analysis["status"] == "success"
        comparisons = analysis["details"]["comparisons"]
        assert len(comparisons) == 1
        assert comparisons[0]["treatment_rate"] > comparisons[0]["control_rate"]
        assert comparisons[0]["relative_lift"] > 0

    def test_analyse_significant_result(self):
        engine = ABTestingEngine()
        result = engine.create_test("camp-1", "Big Test", [
            {"name": "Control", "content": {}, "is_control": True},
            {"name": "Treatment", "content": {}},
        ], confidence_threshold=95.0)
        test_id = result["details"]["id"]
        control_id = result["details"]["variants"][0]["id"]
        treatment_id = result["details"]["variants"][1]["id"]
        engine.start_test(test_id)

        # Large sample with clear difference
        engine.record_event(test_id, control_id, "send", count=5000)
        engine.record_event(test_id, control_id, "click", count=100)   # 2%
        engine.record_event(test_id, treatment_id, "send", count=5000)
        engine.record_event(test_id, treatment_id, "click", count=200)  # 4%

        analysis = engine.analyse_test(test_id)
        comparisons = analysis["details"]["comparisons"]
        assert comparisons[0]["is_significant"] is True
        assert comparisons[0]["confidence"] >= 95.0
        assert analysis["details"]["winner"] is not None

    def test_stop_test(self):
        engine = ABTestingEngine()
        result = engine.create_test("camp-1", "Test", [
            {"name": "A", "content": {}, "is_control": True},
            {"name": "B", "content": {}},
        ])
        test_id = result["details"]["id"]
        engine.start_test(test_id)
        stop_result = engine.stop_test(test_id)
        assert stop_result["status"] == "success"

    def test_pause_test(self):
        engine = ABTestingEngine()
        result = engine.create_test("camp-1", "Test", [
            {"name": "A", "content": {}, "is_control": True},
            {"name": "B", "content": {}},
        ])
        test_id = result["details"]["id"]
        engine.start_test(test_id)
        pause_result = engine.pause_test(test_id)
        assert pause_result["status"] == "success"

    def test_list_tests(self):
        engine = ABTestingEngine()
        engine.create_test("camp-1", "Test 1", [{"name": "A"}, {"name": "B"}])
        engine.create_test("camp-2", "Test 2", [{"name": "A"}, {"name": "B"}])
        tests = engine.list_tests()
        assert len(tests) == 2

    def test_list_tests_filter_campaign(self):
        engine = ABTestingEngine()
        engine.create_test("camp-1", "Test 1", [{"name": "A"}, {"name": "B"}])
        engine.create_test("camp-2", "Test 2", [{"name": "A"}, {"name": "B"}])
        tests = engine.list_tests(campaign_id="camp-1")
        assert len(tests) == 1

    def test_calculate_sample_size(self):
        engine = ABTestingEngine()
        result = engine.calculate_sample_size(baseline_rate=0.025, minimum_detectable_effect=0.1)
        assert result["sample_size_per_variant"] > 0
        assert result["total_sample_size"] == result["sample_size_per_variant"] * 2

    def test_record_events_batch(self):
        engine = ABTestingEngine()
        result = engine.create_test("camp-1", "Test", [
            {"name": "A", "content": {}, "is_control": True},
            {"name": "B", "content": {}},
        ])
        test_id = result["details"]["id"]
        variant_a = result["details"]["variants"][0]["id"]
        engine.start_test(test_id)

        batch_result = engine.record_events_batch(test_id, [
            {"variant_id": variant_a, "event_type": "send", "count": 50},
            {"variant_id": variant_a, "event_type": "open", "count": 10},
        ])
        assert batch_result["status"] == "success"


# ===========================================================================
# Test Statistical Calculator
# ===========================================================================

class TestStatisticalCalculator:
    """Tests for the statistical utility functions."""

    def test_z_score_equal_proportions(self):
        z = StatisticalCalculator.z_score(0.05, 0.05, 1000, 1000)
        assert abs(z) < 0.01

    def test_z_score_different_proportions(self):
        z = StatisticalCalculator.z_score(0.02, 0.04, 5000, 5000)
        assert z > 0  # Treatment is better

    def test_z_score_zero_samples(self):
        z = StatisticalCalculator.z_score(0.05, 0.10, 0, 0)
        assert z == 0.0

    def test_p_value_from_z(self):
        # z=0 should give p=1
        assert abs(StatisticalCalculator.p_value_from_z(0) - 1.0) < 0.01
        # z=1.96 should give p≈0.05
        p = StatisticalCalculator.p_value_from_z(1.96)
        assert 0.04 < p < 0.06
        # z=2.576 should give p≈0.01
        p = StatisticalCalculator.p_value_from_z(2.576)
        assert 0.005 < p < 0.015

    def test_confidence_level(self):
        assert StatisticalCalculator.confidence_level(0.05) == pytest.approx(95.0, abs=0.1)
        assert StatisticalCalculator.confidence_level(0.01) == pytest.approx(99.0, abs=0.1)
        assert StatisticalCalculator.confidence_level(1.0) == 0.0

    def test_minimum_sample_size(self):
        n = StatisticalCalculator.minimum_sample_size(0.025, 0.1)
        assert n > 0
        # Larger effect should need smaller sample
        n_large = StatisticalCalculator.minimum_sample_size(0.025, 0.5)
        assert n_large < n

    def test_relative_lift(self):
        assert StatisticalCalculator.relative_lift(0.02, 0.04) == pytest.approx(1.0, abs=0.01)
        assert StatisticalCalculator.relative_lift(0.0, 0.04) == 0.0
