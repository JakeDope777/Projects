"""
Smart Segmentation Engine

Automatically segments leads based on behaviour, demographics, engagement
scores, and custom rules. Supports both rule-based and clustering-based
segmentation strategies.

Features:
- Rule-based segmentation with composable conditions
- Behaviour-based auto-segmentation (RFM analysis)
- Engagement-tier segmentation
- Demographic segmentation
- Dynamic segments that auto-update as lead data changes
- Segment overlap analysis
- Segment performance comparison
"""

import uuid
import math
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from enum import Enum
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enums & types
# ---------------------------------------------------------------------------

class SegmentType(str, Enum):
    RULE_BASED = "rule_based"
    BEHAVIORAL = "behavioral"
    DEMOGRAPHIC = "demographic"
    ENGAGEMENT = "engagement"
    RFM = "rfm"
    CUSTOM = "custom"


class Operator(str, Enum):
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_OR_EQUAL = "greater_or_equal"
    LESS_OR_EQUAL = "less_or_equal"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    IN = "in"
    NOT_IN = "not_in"
    EXISTS = "exists"
    NOT_EXISTS = "not_exists"
    BETWEEN = "between"


class LogicOperator(str, Enum):
    AND = "and"
    OR = "or"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class SegmentRule:
    """A single condition in a segment definition."""
    field: str
    operator: Operator
    value: object = None
    value_secondary: object = None  # For BETWEEN operator

    def evaluate(self, lead: dict) -> bool:
        """Evaluate this rule against a lead."""
        lead_value = self._get_nested_value(lead, self.field)

        if self.operator == Operator.EXISTS:
            return lead_value is not None
        if self.operator == Operator.NOT_EXISTS:
            return lead_value is None

        if lead_value is None:
            return False

        try:
            if self.operator == Operator.EQUALS:
                return lead_value == self.value
            elif self.operator == Operator.NOT_EQUALS:
                return lead_value != self.value
            elif self.operator == Operator.GREATER_THAN:
                return float(lead_value) > float(self.value)
            elif self.operator == Operator.LESS_THAN:
                return float(lead_value) < float(self.value)
            elif self.operator == Operator.GREATER_OR_EQUAL:
                return float(lead_value) >= float(self.value)
            elif self.operator == Operator.LESS_OR_EQUAL:
                return float(lead_value) <= float(self.value)
            elif self.operator == Operator.CONTAINS:
                return str(self.value).lower() in str(lead_value).lower()
            elif self.operator == Operator.NOT_CONTAINS:
                return str(self.value).lower() not in str(lead_value).lower()
            elif self.operator == Operator.IN:
                return lead_value in (self.value if isinstance(self.value, list) else [self.value])
            elif self.operator == Operator.NOT_IN:
                return lead_value not in (self.value if isinstance(self.value, list) else [self.value])
            elif self.operator == Operator.BETWEEN:
                return float(self.value) <= float(lead_value) <= float(self.value_secondary)
        except (ValueError, TypeError):
            return False

        return False

    @staticmethod
    def _get_nested_value(data: dict, field_path: str):
        """Get a value from a nested dict using dot notation."""
        keys = field_path.split(".")
        current = data
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key)
            else:
                return None
        return current

    def to_dict(self) -> dict:
        return {
            "field": self.field,
            "operator": self.operator.value,
            "value": self.value,
            "value_secondary": self.value_secondary,
        }


@dataclass
class SegmentDefinition:
    """A segment definition with rules and metadata."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    segment_type: SegmentType = SegmentType.RULE_BASED
    rules: list[SegmentRule] = field(default_factory=list)
    logic: LogicOperator = LogicOperator.AND
    is_dynamic: bool = True
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict = field(default_factory=dict)

    def evaluate(self, lead: dict) -> bool:
        """Check if a lead matches this segment."""
        if not self.rules:
            return False
        if self.logic == LogicOperator.AND:
            return all(rule.evaluate(lead) for rule in self.rules)
        else:
            return any(rule.evaluate(lead) for rule in self.rules)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "segment_type": self.segment_type.value,
            "rules": [r.to_dict() for r in self.rules],
            "logic": self.logic.value,
            "is_dynamic": self.is_dynamic,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


# ---------------------------------------------------------------------------
# Pre-built segment templates
# ---------------------------------------------------------------------------

SEGMENT_TEMPLATES = {
    "high_value_leads": {
        "name": "High-Value Leads",
        "description": "Leads with high engagement scores likely to convert",
        "segment_type": SegmentType.ENGAGEMENT,
        "rules": [
            {"field": "score", "operator": "greater_or_equal", "value": 70},
            {"field": "engagement.email_clicks", "operator": "greater_than", "value": 5},
        ],
        "logic": "and",
    },
    "cold_leads": {
        "name": "Cold Leads",
        "description": "Leads with minimal engagement needing re-activation",
        "segment_type": SegmentType.ENGAGEMENT,
        "rules": [
            {"field": "score", "operator": "less_than", "value": 20},
            {"field": "behavior.days_since_last_activity", "operator": "greater_than", "value": 60},
        ],
        "logic": "and",
    },
    "enterprise_prospects": {
        "name": "Enterprise Prospects",
        "description": "Large company leads with decision-making authority",
        "segment_type": SegmentType.DEMOGRAPHIC,
        "rules": [
            {"field": "demographics.company_size", "operator": "in",
             "value": ["1001-5000", "5001-10000", "10000+"]},
            {"field": "demographics.job_title", "operator": "contains", "value": "director"},
        ],
        "logic": "or",
    },
    "smb_segment": {
        "name": "SMB Segment",
        "description": "Small and medium business leads",
        "segment_type": SegmentType.DEMOGRAPHIC,
        "rules": [
            {"field": "demographics.company_size", "operator": "in",
             "value": ["1-10", "11-50", "51-200"]},
        ],
        "logic": "and",
    },
    "trial_users": {
        "name": "Active Trial Users",
        "description": "Leads currently in a product trial",
        "segment_type": SegmentType.BEHAVIORAL,
        "rules": [
            {"field": "behavior.trial_signup", "operator": "equals", "value": True},
            {"field": "status", "operator": "not_equals", "value": "converted"},
        ],
        "logic": "and",
    },
    "at_risk_customers": {
        "name": "At-Risk Customers",
        "description": "Customers showing signs of churn",
        "segment_type": SegmentType.BEHAVIORAL,
        "rules": [
            {"field": "status", "operator": "equals", "value": "customer"},
            {"field": "behavior.days_since_last_activity", "operator": "greater_than", "value": 30},
            {"field": "engagement.email_opens", "operator": "less_than", "value": 2},
        ],
        "logic": "and",
    },
    "marketing_qualified": {
        "name": "Marketing Qualified Leads (MQL)",
        "description": "Leads that meet marketing qualification criteria",
        "segment_type": SegmentType.ENGAGEMENT,
        "rules": [
            {"field": "score", "operator": "between", "value": 40, "value_secondary": 69},
            {"field": "engagement.form_submissions", "operator": "greater_than", "value": 0},
        ],
        "logic": "and",
    },
    "sales_qualified": {
        "name": "Sales Qualified Leads (SQL)",
        "description": "Leads ready for sales outreach",
        "segment_type": SegmentType.ENGAGEMENT,
        "rules": [
            {"field": "score", "operator": "greater_or_equal", "value": 70},
            {"field": "engagement.demo_requests", "operator": "greater_than", "value": 0},
        ],
        "logic": "and",
    },
    "geo_tier1": {
        "name": "Tier 1 Geography",
        "description": "Leads from primary target markets",
        "segment_type": SegmentType.DEMOGRAPHIC,
        "rules": [
            {"field": "demographics.country", "operator": "in",
             "value": ["us", "uk", "canada", "germany", "australia"]},
        ],
        "logic": "and",
    },
    "recent_engaged": {
        "name": "Recently Engaged",
        "description": "Leads who engaged in the last 7 days",
        "segment_type": SegmentType.BEHAVIORAL,
        "rules": [
            {"field": "behavior.days_since_last_activity", "operator": "less_or_equal", "value": 7},
        ],
        "logic": "and",
    },
}


# ---------------------------------------------------------------------------
# RFM Analysis
# ---------------------------------------------------------------------------

class RFMAnalyser:
    """
    Recency-Frequency-Monetary analysis for customer segmentation.
    Assigns each lead an RFM score and segment label.
    """

    RFM_SEGMENTS = {
        (5, 5, 5): "Champions",
        (5, 5, 4): "Champions",
        (5, 4, 5): "Champions",
        (4, 5, 5): "Loyal Customers",
        (4, 4, 5): "Loyal Customers",
        (5, 4, 4): "Loyal Customers",
        (5, 3, 3): "Potential Loyalists",
        (4, 3, 3): "Potential Loyalists",
        (4, 4, 3): "Potential Loyalists",
        (5, 1, 1): "New Customers",
        (4, 1, 1): "New Customers",
        (3, 3, 3): "Promising",
        (3, 2, 2): "Promising",
        (2, 3, 3): "Need Attention",
        (2, 2, 3): "Need Attention",
        (3, 1, 1): "About to Sleep",
        (2, 2, 2): "About to Sleep",
        (1, 3, 3): "At Risk",
        (1, 2, 3): "At Risk",
        (1, 3, 2): "At Risk",
        (1, 1, 3): "Can't Lose Them",
        (1, 1, 2): "Hibernating",
        (1, 1, 1): "Lost",
        (1, 2, 1): "Lost",
        (2, 1, 1): "Lost",
    }

    @classmethod
    def analyse(cls, leads: list[dict]) -> list[dict]:
        """Perform RFM analysis on a list of leads."""
        if not leads:
            return []

        # Extract raw RFM values
        rfm_data = []
        for lead in leads:
            behavior = lead.get("behavior", {})
            engagement = lead.get("engagement", {})

            recency = behavior.get("days_since_last_activity", 999)
            frequency = (
                engagement.get("email_clicks", 0) +
                engagement.get("website_visits", 0) +
                engagement.get("form_submissions", 0)
            )
            monetary = engagement.get("content_downloads", 0) * 10 + \
                       engagement.get("demo_requests", 0) * 50

            rfm_data.append({
                "lead_id": lead.get("id", "unknown"),
                "recency_raw": recency,
                "frequency_raw": frequency,
                "monetary_raw": monetary,
            })

        # Score each dimension 1-5 using quintiles
        for dimension in ["recency_raw", "frequency_raw", "monetary_raw"]:
            values = sorted(set(d[dimension] for d in rfm_data))
            n = len(values)
            for entry in rfm_data:
                val = entry[dimension]
                rank = values.index(val)
                if dimension == "recency_raw":
                    # Lower recency = better (more recent)
                    score = 5 - int((rank / max(n, 1)) * 5)
                else:
                    score = 1 + int((rank / max(n, 1)) * 4)
                score = max(1, min(5, score))
                entry[dimension.replace("_raw", "_score")] = score

        # Assign segments
        results = []
        for entry in rfm_data:
            r = entry["recency_score"]
            f = entry["frequency_score"]
            m = entry["monetary_score"]

            # Find closest matching segment
            segment = cls._find_segment(r, f, m)

            results.append({
                "lead_id": entry["lead_id"],
                "recency_score": r,
                "frequency_score": f,
                "monetary_score": m,
                "rfm_score": r * 100 + f * 10 + m,
                "segment": segment,
            })

        return results

    @classmethod
    def _find_segment(cls, r: int, f: int, m: int) -> str:
        """Find the best matching RFM segment."""
        key = (r, f, m)
        if key in cls.RFM_SEGMENTS:
            return cls.RFM_SEGMENTS[key]

        # Find closest match
        best_dist = float("inf")
        best_segment = "Promising"
        for (kr, kf, km), segment in cls.RFM_SEGMENTS.items():
            dist = abs(r - kr) + abs(f - kf) + abs(m - km)
            if dist < best_dist:
                best_dist = dist
                best_segment = segment
        return best_segment


# ---------------------------------------------------------------------------
# Segmentation engine
# ---------------------------------------------------------------------------

class SegmentationEngine:
    """
    Manages segment definitions, evaluates leads against segments,
    and provides segment analytics.
    """

    def __init__(self):
        self._segments: dict[str, SegmentDefinition] = {}
        self._segment_members: dict[str, set[str]] = {}  # segment_id -> set of lead_ids
        self._rfm_analyser = RFMAnalyser()

    # ---- Segment management ------------------------------------------------

    def create_segment(self, name: str, rules: list[dict],
                       logic: str = "and",
                       segment_type: str = "rule_based",
                       description: str = "",
                       is_dynamic: bool = True) -> dict:
        """Create a new segment definition."""
        parsed_rules = []
        for rule_dict in rules:
            parsed_rules.append(SegmentRule(
                field=rule_dict["field"],
                operator=Operator(rule_dict["operator"]),
                value=rule_dict.get("value"),
                value_secondary=rule_dict.get("value_secondary"),
            ))

        segment = SegmentDefinition(
            name=name,
            description=description,
            segment_type=SegmentType(segment_type),
            rules=parsed_rules,
            logic=LogicOperator(logic),
            is_dynamic=is_dynamic,
        )
        self._segments[segment.id] = segment
        self._segment_members[segment.id] = set()

        return {
            "status": "success",
            "details": segment.to_dict(),
            "logs": [f"Segment '{name}' created with ID {segment.id}"],
        }

    def create_from_template(self, template_id: str) -> dict:
        """Create a segment from a pre-built template."""
        if template_id not in SEGMENT_TEMPLATES:
            return {
                "status": "error",
                "details": {"message": f"Unknown template: {template_id}"},
                "logs": [],
            }

        template = SEGMENT_TEMPLATES[template_id]
        return self.create_segment(
            name=template["name"],
            rules=template["rules"],
            logic=template.get("logic", "and"),
            segment_type=template.get("segment_type", "rule_based"),
            description=template.get("description", ""),
        )

    def get_segment(self, segment_id: str) -> Optional[dict]:
        """Get a segment definition."""
        segment = self._segments.get(segment_id)
        if segment:
            result = segment.to_dict()
            result["member_count"] = len(self._segment_members.get(segment_id, set()))
            return result
        return None

    def list_segments(self) -> list[dict]:
        """List all segments with member counts."""
        results = []
        for seg_id, segment in self._segments.items():
            info = segment.to_dict()
            info["member_count"] = len(self._segment_members.get(seg_id, set()))
            results.append(info)
        return results

    def delete_segment(self, segment_id: str) -> dict:
        """Delete a segment."""
        if segment_id in self._segments:
            name = self._segments[segment_id].name
            del self._segments[segment_id]
            self._segment_members.pop(segment_id, None)
            return {"status": "success", "logs": [f"Segment '{name}' deleted"]}
        return {"status": "not_found"}

    # ---- Evaluation --------------------------------------------------------

    def evaluate_lead(self, lead: dict) -> list[dict]:
        """Evaluate a lead against all segments and return matching ones."""
        matches = []
        for seg_id, segment in self._segments.items():
            if segment.evaluate(lead):
                lead_id = lead.get("id", "unknown")
                self._segment_members.setdefault(seg_id, set()).add(lead_id)
                matches.append({
                    "segment_id": seg_id,
                    "segment_name": segment.name,
                    "segment_type": segment.segment_type.value,
                })
            else:
                lead_id = lead.get("id", "unknown")
                self._segment_members.get(seg_id, set()).discard(lead_id)
        return matches

    def evaluate_leads_batch(self, leads: list[dict]) -> dict:
        """Evaluate multiple leads against all segments."""
        results = {}
        for lead in leads:
            lead_id = lead.get("id", "unknown")
            results[lead_id] = self.evaluate_lead(lead)
        return results

    def get_segment_members(self, segment_id: str) -> list[str]:
        """Get all lead IDs in a segment."""
        return list(self._segment_members.get(segment_id, set()))

    # ---- Auto-segmentation -------------------------------------------------

    def auto_segment_by_engagement(self, leads: list[dict]) -> dict:
        """Automatically segment leads into engagement tiers."""
        tiers = {
            "highly_engaged": [],
            "moderately_engaged": [],
            "low_engagement": [],
            "disengaged": [],
        }

        for lead in leads:
            score = lead.get("score", 0)
            lead_id = lead.get("id", "unknown")

            if score >= 70:
                tiers["highly_engaged"].append(lead_id)
            elif score >= 40:
                tiers["moderately_engaged"].append(lead_id)
            elif score >= 15:
                tiers["low_engagement"].append(lead_id)
            else:
                tiers["disengaged"].append(lead_id)

        return {
            "tiers": {k: {"count": len(v), "lead_ids": v} for k, v in tiers.items()},
            "total_leads": len(leads),
        }

    def auto_segment_rfm(self, leads: list[dict]) -> list[dict]:
        """Perform RFM-based auto-segmentation."""
        return self._rfm_analyser.analyse(leads)

    # ---- Analytics ---------------------------------------------------------

    def get_segment_overlap(self) -> dict:
        """Analyse overlap between segments."""
        overlaps = {}
        segment_ids = list(self._segment_members.keys())

        for i, seg_a in enumerate(segment_ids):
            for seg_b in segment_ids[i + 1:]:
                members_a = self._segment_members.get(seg_a, set())
                members_b = self._segment_members.get(seg_b, set())
                overlap = members_a & members_b

                if overlap:
                    name_a = self._segments[seg_a].name if seg_a in self._segments else seg_a
                    name_b = self._segments[seg_b].name if seg_b in self._segments else seg_b
                    overlaps[f"{name_a} ∩ {name_b}"] = {
                        "overlap_count": len(overlap),
                        "segment_a_count": len(members_a),
                        "segment_b_count": len(members_b),
                        "jaccard_index": round(
                            len(overlap) / max(len(members_a | members_b), 1), 4
                        ),
                    }

        return overlaps

    def get_segment_stats(self) -> dict:
        """Get summary statistics for all segments."""
        total_leads_in_segments = set()
        stats = []

        for seg_id, segment in self._segments.items():
            members = self._segment_members.get(seg_id, set())
            total_leads_in_segments.update(members)
            stats.append({
                "segment_id": seg_id,
                "name": segment.name,
                "type": segment.segment_type.value,
                "member_count": len(members),
                "is_dynamic": segment.is_dynamic,
            })

        return {
            "total_segments": len(self._segments),
            "total_unique_leads": len(total_leads_in_segments),
            "segments": stats,
        }

    def get_available_templates(self) -> dict:
        """Return all available segment templates."""
        return {
            tid: {
                "name": t["name"],
                "description": t["description"],
                "type": t.get("segment_type", "rule_based"),
                "rule_count": len(t["rules"]),
            }
            for tid, t in SEGMENT_TEMPLATES.items()
        }
