"""
Customer Journey Mapping Engine

Visualises and manages the customer lifecycle from initial awareness through
to advocacy. Tracks leads through defined stages, records touchpoints,
and provides analytics on journey progression and drop-off.

Stages:
  Awareness → Interest → Consideration → Intent → Evaluation → Purchase →
  Onboarding → Adoption → Retention → Expansion → Advocacy

Features:
- Define and customise journey stages
- Track lead progression through stages
- Record touchpoints with channel attribution
- Identify bottlenecks and drop-off points
- Journey analytics and funnel metrics
- Stage-based automation triggers
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import Optional
from enum import Enum
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Journey stage definitions
# ---------------------------------------------------------------------------

class JourneyStage(str, Enum):
    """Standard customer journey stages."""
    AWARENESS = "awareness"
    INTEREST = "interest"
    CONSIDERATION = "consideration"
    INTENT = "intent"
    EVALUATION = "evaluation"
    PURCHASE = "purchase"
    ONBOARDING = "onboarding"
    ADOPTION = "adoption"
    RETENTION = "retention"
    EXPANSION = "expansion"
    ADVOCACY = "advocacy"


# Ordered list for progression tracking
STAGE_ORDER = [
    JourneyStage.AWARENESS,
    JourneyStage.INTEREST,
    JourneyStage.CONSIDERATION,
    JourneyStage.INTENT,
    JourneyStage.EVALUATION,
    JourneyStage.PURCHASE,
    JourneyStage.ONBOARDING,
    JourneyStage.ADOPTION,
    JourneyStage.RETENTION,
    JourneyStage.EXPANSION,
    JourneyStage.ADVOCACY,
]

STAGE_INDEX = {stage: idx for idx, stage in enumerate(STAGE_ORDER)}


# Default stage configuration
DEFAULT_STAGE_CONFIG = {
    JourneyStage.AWARENESS: {
        "description": "Lead becomes aware of the brand or product",
        "typical_channels": ["social_media", "content_marketing", "paid_ads", "seo"],
        "key_metrics": ["impressions", "reach", "brand_mentions"],
        "exit_criteria": {"min_touchpoints": 1},
        "recommended_actions": ["serve_educational_content", "retarget_ads"],
    },
    JourneyStage.INTEREST: {
        "description": "Lead shows active interest by engaging with content",
        "typical_channels": ["blog", "email_signup", "social_engagement", "webinar"],
        "key_metrics": ["email_signups", "content_downloads", "time_on_site"],
        "exit_criteria": {"min_touchpoints": 2, "min_engagement_score": 10},
        "recommended_actions": ["send_welcome_email", "offer_lead_magnet"],
    },
    JourneyStage.CONSIDERATION: {
        "description": "Lead actively researches and compares solutions",
        "typical_channels": ["case_studies", "comparison_pages", "reviews", "email_nurture"],
        "key_metrics": ["case_study_views", "comparison_page_visits", "email_engagement"],
        "exit_criteria": {"min_touchpoints": 3, "min_engagement_score": 25},
        "recommended_actions": ["send_case_studies", "invite_to_webinar"],
    },
    JourneyStage.INTENT: {
        "description": "Lead demonstrates purchase intent",
        "typical_channels": ["pricing_page", "demo_request", "sales_call", "free_trial"],
        "key_metrics": ["pricing_page_visits", "demo_requests", "trial_signups"],
        "exit_criteria": {"min_touchpoints": 1, "required_actions": ["pricing_view"]},
        "recommended_actions": ["offer_demo", "send_roi_calculator"],
    },
    JourneyStage.EVALUATION: {
        "description": "Lead evaluates the product through trial or demo",
        "typical_channels": ["product_trial", "demo", "sales_meeting", "proposal"],
        "key_metrics": ["trial_usage", "feature_adoption", "meeting_count"],
        "exit_criteria": {"min_touchpoints": 2, "min_engagement_score": 50},
        "recommended_actions": ["personalised_demo", "send_proposal", "address_objections"],
    },
    JourneyStage.PURCHASE: {
        "description": "Lead converts to a paying customer",
        "typical_channels": ["checkout", "contract_signing", "payment"],
        "key_metrics": ["conversion_rate", "deal_value", "time_to_close"],
        "exit_criteria": {"required_actions": ["purchase_completed"]},
        "recommended_actions": ["send_confirmation", "begin_onboarding"],
    },
    JourneyStage.ONBOARDING: {
        "description": "New customer is set up and guided to first value",
        "typical_channels": ["onboarding_email", "setup_wizard", "training", "support"],
        "key_metrics": ["setup_completion", "time_to_first_value", "support_tickets"],
        "exit_criteria": {"required_actions": ["setup_completed"]},
        "recommended_actions": ["guided_setup", "assign_csm", "schedule_training"],
    },
    JourneyStage.ADOPTION: {
        "description": "Customer regularly uses the product and derives value",
        "typical_channels": ["product_usage", "feature_discovery", "support", "community"],
        "key_metrics": ["dau_mau_ratio", "feature_usage", "health_score"],
        "exit_criteria": {"min_engagement_score": 60, "min_days": 30},
        "recommended_actions": ["feature_education", "usage_tips", "check_in"],
    },
    JourneyStage.RETENTION: {
        "description": "Customer renews and continues to find value",
        "typical_channels": ["renewal", "qbr", "product_updates", "loyalty_programme"],
        "key_metrics": ["renewal_rate", "nps_score", "support_satisfaction"],
        "exit_criteria": {"required_actions": ["renewal_completed"]},
        "recommended_actions": ["renewal_outreach", "qbr_scheduling", "loyalty_rewards"],
    },
    JourneyStage.EXPANSION: {
        "description": "Customer expands usage through upsell or cross-sell",
        "typical_channels": ["upsell_email", "account_review", "new_feature_launch"],
        "key_metrics": ["expansion_revenue", "seats_added", "features_adopted"],
        "exit_criteria": {"required_actions": ["expansion_purchase"]},
        "recommended_actions": ["upsell_offer", "cross_sell_recommendation", "account_review"],
    },
    JourneyStage.ADVOCACY: {
        "description": "Customer actively promotes the brand to others",
        "typical_channels": ["referral", "review", "case_study", "speaking", "community"],
        "key_metrics": ["referrals_made", "reviews_written", "nps_score"],
        "exit_criteria": {},
        "recommended_actions": ["referral_programme", "case_study_request", "community_invite"],
    },
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Touchpoint:
    """A single interaction in the customer journey."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    lead_id: str = ""
    stage: str = ""
    channel: str = ""
    action: str = ""
    details: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    attribution_weight: float = 1.0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "lead_id": self.lead_id,
            "stage": self.stage,
            "channel": self.channel,
            "action": self.action,
            "details": self.details,
            "timestamp": self.timestamp,
            "attribution_weight": self.attribution_weight,
        }


@dataclass
class JourneyState:
    """Current journey state for a lead."""
    lead_id: str
    current_stage: JourneyStage = JourneyStage.AWARENESS
    stage_entered_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    touchpoints: list[Touchpoint] = field(default_factory=list)
    stage_history: list[dict] = field(default_factory=list)
    tags: set = field(default_factory=set)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "lead_id": self.lead_id,
            "current_stage": self.current_stage.value,
            "stage_entered_at": self.stage_entered_at,
            "touchpoint_count": len(self.touchpoints),
            "stage_history": self.stage_history,
            "tags": list(self.tags),
        }


# ---------------------------------------------------------------------------
# Journey mapping engine
# ---------------------------------------------------------------------------

class JourneyMapper:
    """
    Manages customer journey tracking, stage progression, and analytics.
    """

    def __init__(self, stage_config: Optional[dict] = None):
        self._stage_config = stage_config or DEFAULT_STAGE_CONFIG
        self._journeys: dict[str, JourneyState] = {}

    # ---- Journey management ------------------------------------------------

    def initialise_journey(self, lead_id: str,
                           initial_stage: JourneyStage = JourneyStage.AWARENESS,
                           metadata: Optional[dict] = None) -> dict:
        """Start tracking a lead's journey."""
        now = datetime.now(timezone.utc).isoformat()
        journey = JourneyState(
            lead_id=lead_id,
            current_stage=initial_stage,
            stage_entered_at=now,
            stage_history=[{
                "stage": initial_stage.value,
                "entered_at": now,
                "exited_at": None,
            }],
            metadata=metadata or {},
        )
        self._journeys[lead_id] = journey
        return {
            "status": "success",
            "details": journey.to_dict(),
            "logs": [f"Journey initialised for lead {lead_id} at stage {initial_stage.value}"],
        }

    def record_touchpoint(self, lead_id: str, channel: str, action: str,
                          details: Optional[dict] = None,
                          attribution_weight: float = 1.0) -> dict:
        """Record a touchpoint in the lead's journey."""
        if lead_id not in self._journeys:
            self.initialise_journey(lead_id)

        journey = self._journeys[lead_id]
        touchpoint = Touchpoint(
            lead_id=lead_id,
            stage=journey.current_stage.value,
            channel=channel,
            action=action,
            details=details or {},
            attribution_weight=attribution_weight,
        )
        journey.touchpoints.append(touchpoint)

        return {
            "status": "success",
            "details": touchpoint.to_dict(),
            "logs": [f"Touchpoint recorded: {channel}/{action} for lead {lead_id}"],
        }

    def advance_stage(self, lead_id: str,
                      target_stage: Optional[JourneyStage] = None) -> dict:
        """Move a lead to the next stage (or a specific stage)."""
        if lead_id not in self._journeys:
            return {
                "status": "error",
                "details": {"message": f"No journey found for lead {lead_id}"},
                "logs": [],
            }

        journey = self._journeys[lead_id]
        current_idx = STAGE_INDEX.get(journey.current_stage, 0)

        if target_stage:
            target_idx = STAGE_INDEX.get(target_stage, current_idx + 1)
        else:
            target_idx = current_idx + 1

        if target_idx >= len(STAGE_ORDER):
            return {
                "status": "already_at_final_stage",
                "details": {"current_stage": journey.current_stage.value},
                "logs": [f"Lead {lead_id} is already at the final stage"],
            }

        now = datetime.now(timezone.utc).isoformat()
        old_stage = journey.current_stage
        new_stage = STAGE_ORDER[target_idx]

        # Close current stage in history
        if journey.stage_history:
            journey.stage_history[-1]["exited_at"] = now

        # Enter new stage
        journey.current_stage = new_stage
        journey.stage_entered_at = now
        journey.stage_history.append({
            "stage": new_stage.value,
            "entered_at": now,
            "exited_at": None,
        })

        return {
            "status": "success",
            "details": {
                "lead_id": lead_id,
                "previous_stage": old_stage.value,
                "current_stage": new_stage.value,
                "stage_config": self._get_stage_info(new_stage),
            },
            "logs": [f"Lead {lead_id} advanced from {old_stage.value} to {new_stage.value}"],
        }

    def get_journey(self, lead_id: str) -> Optional[dict]:
        """Get the full journey state for a lead."""
        journey = self._journeys.get(lead_id)
        if not journey:
            return None
        result = journey.to_dict()
        result["touchpoints"] = [tp.to_dict() for tp in journey.touchpoints]
        result["current_stage_config"] = self._get_stage_info(journey.current_stage)
        return result

    # ---- Analytics ---------------------------------------------------------

    def get_funnel_metrics(self) -> dict:
        """Calculate funnel metrics across all journeys."""
        stage_counts: dict[str, int] = {stage.value: 0 for stage in STAGE_ORDER}
        stage_ever_reached: dict[str, int] = {stage.value: 0 for stage in STAGE_ORDER}
        total_journeys = len(self._journeys)

        for journey in self._journeys.values():
            # Current stage
            stage_counts[journey.current_stage.value] += 1
            # All stages ever reached
            for entry in journey.stage_history:
                stage_ever_reached[entry["stage"]] += 1

        # Conversion rates between stages
        conversion_rates = {}
        for i in range(len(STAGE_ORDER) - 1):
            from_stage = STAGE_ORDER[i].value
            to_stage = STAGE_ORDER[i + 1].value
            from_count = stage_ever_reached.get(from_stage, 0)
            to_count = stage_ever_reached.get(to_stage, 0)
            rate = to_count / max(from_count, 1)
            conversion_rates[f"{from_stage}_to_{to_stage}"] = round(rate, 4)

        return {
            "total_journeys": total_journeys,
            "current_stage_distribution": stage_counts,
            "stage_ever_reached": stage_ever_reached,
            "stage_conversion_rates": conversion_rates,
        }

    def get_bottlenecks(self) -> list[dict]:
        """Identify stages with the highest drop-off rates."""
        funnel = self.get_funnel_metrics()
        conversion_rates = funnel.get("stage_conversion_rates", {})

        bottlenecks = []
        for transition, rate in conversion_rates.items():
            if rate < 0.5:  # Less than 50% conversion
                from_stage, to_stage = transition.split("_to_")
                bottlenecks.append({
                    "from_stage": from_stage,
                    "to_stage": to_stage,
                    "conversion_rate": rate,
                    "severity": "critical" if rate < 0.2 else "warning",
                    "recommendation": self._bottleneck_recommendation(from_stage, rate),
                })

        bottlenecks.sort(key=lambda b: b["conversion_rate"])
        return bottlenecks

    def get_stage_duration_stats(self) -> dict:
        """Calculate average time spent in each stage."""
        durations: dict[str, list[float]] = {stage.value: [] for stage in STAGE_ORDER}

        for journey in self._journeys.values():
            for entry in journey.stage_history:
                entered = entry.get("entered_at")
                exited = entry.get("exited_at")
                if entered and exited:
                    try:
                        entered_dt = datetime.fromisoformat(entered)
                        exited_dt = datetime.fromisoformat(exited)
                        days = (exited_dt - entered_dt).total_seconds() / 86400
                        durations[entry["stage"]].append(days)
                    except (ValueError, TypeError):
                        pass

        stats = {}
        for stage, days_list in durations.items():
            if days_list:
                stats[stage] = {
                    "avg_days": round(sum(days_list) / len(days_list), 2),
                    "min_days": round(min(days_list), 2),
                    "max_days": round(max(days_list), 2),
                    "sample_count": len(days_list),
                }
            else:
                stats[stage] = {"avg_days": None, "sample_count": 0}

        return stats

    def get_channel_attribution(self) -> dict:
        """Analyse which channels contribute most to stage progression."""
        channel_stats: dict[str, dict] = {}

        for journey in self._journeys.values():
            for tp in journey.touchpoints:
                channel = tp.channel
                if channel not in channel_stats:
                    channel_stats[channel] = {
                        "total_touchpoints": 0,
                        "stages": {},
                        "total_weight": 0.0,
                    }
                channel_stats[channel]["total_touchpoints"] += 1
                channel_stats[channel]["total_weight"] += tp.attribution_weight
                stage = tp.stage
                channel_stats[channel]["stages"][stage] = (
                    channel_stats[channel]["stages"].get(stage, 0) + 1
                )

        return channel_stats

    def get_leads_at_stage(self, stage: JourneyStage) -> list[str]:
        """Return all lead IDs currently at a specific stage."""
        return [
            lead_id for lead_id, journey in self._journeys.items()
            if journey.current_stage == stage
        ]

    # ---- Helpers -----------------------------------------------------------

    def _get_stage_info(self, stage: JourneyStage) -> dict:
        """Get configuration info for a stage."""
        config = self._stage_config.get(stage, {})
        return {
            "stage": stage.value,
            "description": config.get("description", ""),
            "typical_channels": config.get("typical_channels", []),
            "key_metrics": config.get("key_metrics", []),
            "recommended_actions": config.get("recommended_actions", []),
        }

    @staticmethod
    def _bottleneck_recommendation(from_stage: str, rate: float) -> str:
        """Generate a recommendation for a bottleneck."""
        recommendations = {
            "awareness": "Increase top-of-funnel content and ad spend to drive more interest",
            "interest": "Improve lead magnets and email capture to move leads to consideration",
            "consideration": "Add more case studies and social proof to build confidence",
            "intent": "Simplify the demo/trial request process and add urgency",
            "evaluation": "Provide better onboarding during trials and address objections proactively",
            "purchase": "Streamline checkout, offer flexible pricing, and reduce friction",
            "onboarding": "Improve setup experience and provide hands-on guidance",
            "adoption": "Drive feature discovery and demonstrate ongoing value",
            "retention": "Proactive outreach before renewal, demonstrate ROI",
            "expansion": "Identify upsell opportunities based on usage patterns",
        }
        return recommendations.get(from_stage, "Review stage experience and identify friction points")

    def get_all_stages(self) -> list[dict]:
        """Return all stage definitions with configuration."""
        return [self._get_stage_info(stage) for stage in STAGE_ORDER]
