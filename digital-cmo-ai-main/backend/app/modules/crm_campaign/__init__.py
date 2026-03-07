# CRM & Campaign Management Module
from .module import CRMCampaignModule
from .lead_scoring import LeadScoringModel, FeatureEngineer
from .workflow_automation import WorkflowEngine, WORKFLOW_TEMPLATES
from .journey_mapping import JourneyMapper, JourneyStage
from .segmentation import SegmentationEngine, RFMAnalyser
from .campaign_predictor import CampaignPredictor
from .compliance import ComplianceEngine
from .ab_testing import ABTestingEngine, StatisticalCalculator

__all__ = [
    "CRMCampaignModule",
    "LeadScoringModel",
    "FeatureEngineer",
    "WorkflowEngine",
    "WORKFLOW_TEMPLATES",
    "JourneyMapper",
    "JourneyStage",
    "SegmentationEngine",
    "RFMAnalyser",
    "CampaignPredictor",
    "ComplianceEngine",
    "ABTestingEngine",
    "StatisticalCalculator",
]
