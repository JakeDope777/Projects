"""
Insight Engine — Automated Narrative Generation & Action Suggestions

Uses LLM to automatically interpret analytics data, narrate what the
numbers mean in plain language, and suggest concrete marketing actions.

Falls back to rule-based insights when LLM is unavailable.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Optional OpenAI import
try:
    from openai import AsyncOpenAI

    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------

@dataclass
class Insight:
    """A single generated insight."""
    category: str  # e.g. "performance", "anomaly", "opportunity", "risk"
    severity: str  # "info", "warning", "critical", "positive"
    title: str
    narrative: str
    suggested_actions: list[str] = field(default_factory=list)
    related_metrics: list[str] = field(default_factory=list)
    confidence: float = 0.0  # 0-1


@dataclass
class InsightReport:
    """Collection of insights for a reporting period."""
    executive_summary: str
    insights: list[Insight]
    generated_at: str = ""
    method: str = "rule_based"  # or "llm"


# ---------------------------------------------------------------------------
# Rule-based insight templates
# ---------------------------------------------------------------------------

_RULES: list[dict[str, Any]] = [
    {
        "condition": lambda m: m.get("ctr", 0) < 1.0,
        "category": "performance",
        "severity": "warning",
        "title": "Low Click-Through Rate",
        "narrative": "CTR is at {ctr}%, which is below the industry average of ~2%. Ad creatives or targeting may need optimization.",
        "actions": [
            "Review and refresh ad creatives with stronger CTAs",
            "Narrow audience targeting to higher-intent segments",
            "A/B test different headlines and images",
        ],
        "metrics": ["ctr", "impressions", "clicks"],
    },
    {
        "condition": lambda m: m.get("cac", 0) > 0 and m.get("ltv", 0) > 0 and m.get("ltv_cac_ratio", 0) < 3.0,
        "category": "risk",
        "severity": "critical",
        "title": "LTV:CAC Ratio Below Healthy Threshold",
        "narrative": "LTV:CAC ratio is {ltv_cac_ratio}x (target: 3x+). Customer acquisition may not be profitable at current costs.",
        "actions": [
            "Reduce CAC by optimizing highest-cost channels",
            "Increase LTV through upselling and retention programs",
            "Focus spend on channels with proven ROI",
        ],
        "metrics": ["ltv", "cac", "ltv_cac_ratio"],
    },
    {
        "condition": lambda m: m.get("churn_rate", 0) > 5.0,
        "category": "risk",
        "severity": "warning",
        "title": "Elevated Churn Rate",
        "narrative": "Churn rate is {churn_rate}%, which exceeds the 5% threshold. Customer retention needs attention.",
        "actions": [
            "Implement a customer success outreach program",
            "Analyze churn reasons through exit surveys",
            "Create re-engagement campaigns for at-risk customers",
        ],
        "metrics": ["churn_rate", "retention_rate"],
    },
    {
        "condition": lambda m: m.get("roas", 0) > 5.0,
        "category": "opportunity",
        "severity": "positive",
        "title": "Strong Return on Ad Spend",
        "narrative": "ROAS is {roas}x, significantly above the 4x benchmark. Consider scaling successful campaigns.",
        "actions": [
            "Increase budget for top-performing campaigns",
            "Expand to similar audience segments",
            "Test higher-funnel campaigns to capture more demand",
        ],
        "metrics": ["roas", "total_revenue", "total_ad_spend"],
    },
    {
        "condition": lambda m: m.get("conversion_rate", 0) < 2.0 and m.get("sessions", 0) > 1000,
        "category": "performance",
        "severity": "warning",
        "title": "Low Conversion Rate Despite Good Traffic",
        "narrative": "Conversion rate is {conversion_rate}% with {sessions} sessions. The funnel may have friction points.",
        "actions": [
            "Audit landing pages for UX issues",
            "Simplify the conversion flow (fewer form fields, clearer CTAs)",
            "Implement exit-intent offers or retargeting",
        ],
        "metrics": ["conversion_rate", "sessions", "conversions"],
    },
    {
        "condition": lambda m: m.get("email_open_rate", 0) < 15.0 and m.get("email_open_rate", 0) > 0,
        "category": "performance",
        "severity": "warning",
        "title": "Below-Average Email Open Rate",
        "narrative": "Email open rate is {email_open_rate}%, below the 20% benchmark. Subject lines or send timing may need work.",
        "actions": [
            "A/B test subject lines with personalization",
            "Optimize send times based on engagement data",
            "Clean email list to remove inactive subscribers",
        ],
        "metrics": ["email_open_rate", "email_click_rate"],
    },
    {
        "condition": lambda m: m.get("bounce_rate", 0) > 60.0,
        "category": "performance",
        "severity": "warning",
        "title": "High Bounce Rate",
        "narrative": "Bounce rate is {bounce_rate}%, indicating visitors leave without engaging. Page relevance or load time may be issues.",
        "actions": [
            "Improve page load speed (target < 3 seconds)",
            "Ensure ad messaging matches landing page content",
            "Add engaging above-the-fold content",
        ],
        "metrics": ["bounce_rate", "avg_session_duration", "pages_per_session"],
    },
    {
        "condition": lambda m: m.get("net_promoter_score", 0) > 50,
        "category": "opportunity",
        "severity": "positive",
        "title": "Excellent Net Promoter Score",
        "narrative": "NPS is {net_promoter_score}, indicating strong customer advocacy. Leverage this for referral programs.",
        "actions": [
            "Launch or expand a referral program",
            "Collect and showcase customer testimonials",
            "Create a customer advocacy program",
        ],
        "metrics": ["net_promoter_score", "referral_rate"],
    },
    {
        "condition": lambda m: m.get("activation_rate", 0) < 30.0 and m.get("signups", 0) > 0,
        "category": "risk",
        "severity": "warning",
        "title": "Low Activation Rate",
        "narrative": "Only {activation_rate}% of signups complete activation. Onboarding experience needs improvement.",
        "actions": [
            "Simplify the onboarding flow",
            "Add in-app guidance and tooltips",
            "Send activation reminder emails within 24 hours",
        ],
        "metrics": ["activation_rate", "onboarding_completion_rate", "signups"],
    },
    {
        "condition": lambda m: m.get("viral_coefficient", 0) > 1.0,
        "category": "opportunity",
        "severity": "positive",
        "title": "Viral Growth Potential",
        "narrative": "Viral coefficient is {viral_coefficient}, meaning each user brings in more than one new user. Growth is self-sustaining.",
        "actions": [
            "Invest in referral program incentives",
            "Make sharing frictionless within the product",
            "Track and optimize the referral funnel",
        ],
        "metrics": ["viral_coefficient", "referral_rate", "referral_conversion_rate"],
    },
]


# ---------------------------------------------------------------------------
# Insight Engine
# ---------------------------------------------------------------------------

class InsightEngine:
    """Generate automated insights from analytics data."""

    def __init__(self, openai_api_key: Optional[str] = None, model: str = "gpt-4.1-mini"):
        self.api_key = openai_api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model
        self._client: Optional[Any] = None

    async def generate_insights(
        self,
        metrics: dict[str, Any],
        period_description: str = "last 30 days",
        use_llm: bool = True,
    ) -> InsightReport:
        """
        Generate insights from computed metrics.

        Args:
            metrics: Dict of KPI name → value.
            period_description: Human-readable period description.
            use_llm: Whether to attempt LLM-based insight generation.

        Returns:
            InsightReport with executive summary and individual insights.
        """
        # Always generate rule-based insights
        rule_insights = self._rule_based_insights(metrics)

        # Attempt LLM enhancement
        if use_llm and self.api_key and HAS_OPENAI:
            try:
                return await self._llm_insights(metrics, rule_insights, period_description)
            except Exception as e:
                logger.warning(f"LLM insight generation failed, using rule-based: {e}")

        # Fallback to rule-based
        summary = self._generate_rule_summary(metrics, rule_insights)
        from datetime import datetime, timezone

        return InsightReport(
            executive_summary=summary,
            insights=rule_insights,
            generated_at=datetime.now(timezone.utc).isoformat(),
            method="rule_based",
        )

    # ------------------------------------------------------------------
    # Rule-based insights
    # ------------------------------------------------------------------

    def _rule_based_insights(self, metrics: dict[str, Any]) -> list[Insight]:
        """Evaluate all rules against current metrics."""
        insights = []
        for rule in _RULES:
            try:
                if rule["condition"](metrics):
                    narrative = rule["narrative"].format(**{
                        k: metrics.get(k, "N/A") for k in rule["metrics"]
                    })
                    insights.append(Insight(
                        category=rule["category"],
                        severity=rule["severity"],
                        title=rule["title"],
                        narrative=narrative,
                        suggested_actions=rule["actions"],
                        related_metrics=rule["metrics"],
                        confidence=0.7,
                    ))
            except (KeyError, TypeError, ValueError):
                continue
        return insights

    def _generate_rule_summary(
        self,
        metrics: dict[str, Any],
        insights: list[Insight],
    ) -> str:
        """Generate a plain-text executive summary from rule-based insights."""
        critical = [i for i in insights if i.severity == "critical"]
        warnings = [i for i in insights if i.severity == "warning"]
        positives = [i for i in insights if i.severity == "positive"]

        parts = []
        if critical:
            parts.append(
                f"CRITICAL: {len(critical)} critical issue(s) detected — "
                + "; ".join(i.title for i in critical) + "."
            )
        if positives:
            parts.append(
                f"POSITIVE: {len(positives)} strength(s) identified — "
                + "; ".join(i.title for i in positives) + "."
            )
        if warnings:
            parts.append(
                f"ATTENTION: {len(warnings)} area(s) need improvement — "
                + "; ".join(i.title for i in warnings) + "."
            )
        if not parts:
            parts.append("All key metrics are within expected ranges. No immediate actions required.")

        return " ".join(parts)

    # ------------------------------------------------------------------
    # LLM-powered insights
    # ------------------------------------------------------------------

    async def _llm_insights(
        self,
        metrics: dict[str, Any],
        rule_insights: list[Insight],
        period_description: str,
    ) -> InsightReport:
        """Use LLM to generate richer, contextual insights."""
        if self._client is None:
            self._client = AsyncOpenAI()

        # Build prompt
        metrics_text = json.dumps(
            {k: v for k, v in metrics.items() if not isinstance(v, dict)},
            indent=2,
        )
        rule_text = "\n".join(
            f"- [{i.severity.upper()}] {i.title}: {i.narrative}"
            for i in rule_insights
        )

        prompt = f"""You are a senior marketing analytics advisor. Analyze the following marketing KPIs 
for the {period_description} and provide actionable insights.

## KPI Data
{metrics_text}

## Preliminary Rule-Based Findings
{rule_text if rule_text else "No rule-based alerts triggered."}

## Instructions
Provide your analysis as a JSON object with this exact structure:
{{
  "executive_summary": "2-3 sentence executive summary of overall marketing performance",
  "insights": [
    {{
      "category": "performance|risk|opportunity|anomaly",
      "severity": "info|warning|critical|positive",
      "title": "Short insight title",
      "narrative": "Detailed explanation of what the data shows and why it matters",
      "suggested_actions": ["Action 1", "Action 2", "Action 3"],
      "related_metrics": ["metric_name_1", "metric_name_2"],
      "confidence": 0.85
    }}
  ]
}}

Focus on:
1. The most impactful findings (both positive and negative)
2. Cross-metric correlations and patterns
3. Specific, actionable recommendations
4. Revenue impact estimation where possible

Return ONLY valid JSON, no markdown formatting."""

        response = await self._client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=2000,
        )

        content = response.choices[0].message.content.strip()
        # Strip markdown code fences if present
        if content.startswith("```"):
            content = content.split("\n", 1)[1]
            if content.endswith("```"):
                content = content[:-3]

        parsed = json.loads(content)

        insights = []
        for item in parsed.get("insights", []):
            insights.append(Insight(
                category=item.get("category", "performance"),
                severity=item.get("severity", "info"),
                title=item.get("title", ""),
                narrative=item.get("narrative", ""),
                suggested_actions=item.get("suggested_actions", []),
                related_metrics=item.get("related_metrics", []),
                confidence=item.get("confidence", 0.8),
            ))

        from datetime import datetime, timezone

        return InsightReport(
            executive_summary=parsed.get("executive_summary", ""),
            insights=insights,
            generated_at=datetime.now(timezone.utc).isoformat(),
            method="llm",
        )
