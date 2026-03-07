"""
Campaign Performance Predictor

Predicts campaign performance metrics before launch using historical data,
audience characteristics, and content analysis. Provides estimated open
rates, click-through rates, conversion rates, and ROI projections.

Features:
- Pre-launch performance prediction (open rate, CTR, conversion)
- Channel-specific benchmarks and adjustments
- Audience quality scoring
- Content effectiveness analysis
- Send-time optimisation recommendations
- ROI projection with confidence intervals
- Historical performance tracking for model improvement
"""

import math
import logging
from datetime import datetime, timezone
from typing import Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Industry benchmarks (based on typical marketing data)
# ---------------------------------------------------------------------------

CHANNEL_BENCHMARKS = {
    "email": {
        "open_rate": 0.215,        # 21.5%
        "click_rate": 0.025,       # 2.5%
        "conversion_rate": 0.012,  # 1.2%
        "unsubscribe_rate": 0.002, # 0.2%
        "bounce_rate": 0.008,      # 0.8%
        "cost_per_send": 0.005,    # $0.005
    },
    "social": {
        "impression_rate": 0.05,   # 5% of followers
        "engagement_rate": 0.032,  # 3.2%
        "click_rate": 0.012,       # 1.2%
        "conversion_rate": 0.008,  # 0.8%
        "cost_per_impression": 0.007,
    },
    "ads": {
        "impression_rate": 1.0,
        "click_rate": 0.019,       # 1.9% CTR
        "conversion_rate": 0.024,  # 2.4%
        "cost_per_click": 1.72,
        "cost_per_impression": 0.005,
    },
    "sms": {
        "delivery_rate": 0.97,
        "open_rate": 0.98,         # 98% open rate for SMS
        "click_rate": 0.19,        # 19% CTR
        "conversion_rate": 0.045,  # 4.5%
        "cost_per_send": 0.015,
    },
}

# Adjustments based on audience characteristics
AUDIENCE_QUALITY_FACTORS = {
    "engagement_high": 1.35,     # Highly engaged audience → +35%
    "engagement_medium": 1.0,    # Average
    "engagement_low": 0.65,      # Low engagement → -35%
    "segment_targeted": 1.25,    # Targeted segment → +25%
    "segment_broad": 0.85,       # Broad audience → -15%
    "list_fresh": 1.15,          # Recently acquired list → +15%
    "list_stale": 0.70,          # Old list → -30%
}

# Content quality factors
CONTENT_FACTORS = {
    "personalised": 1.26,        # Personalisation → +26%
    "generic": 0.85,             # Generic content → -15%
    "has_emoji_subject": 1.04,   # Emoji in subject → +4%
    "has_urgency": 1.15,         # Urgency language → +15%
    "has_offer": 1.20,           # Contains offer/discount → +20%
    "has_social_proof": 1.12,    # Social proof → +12%
    "has_clear_cta": 1.18,       # Clear CTA → +18%
    "mobile_optimised": 1.10,    # Mobile-optimised → +10%
    "long_subject": 0.90,        # Subject > 60 chars → -10%
    "short_subject": 1.05,       # Subject < 30 chars → +5%
}

# Send time adjustments (hour of day, UTC)
SEND_TIME_FACTORS = {
    6: 0.90, 7: 0.95, 8: 1.05, 9: 1.15, 10: 1.20,
    11: 1.10, 12: 0.95, 13: 1.00, 14: 1.05, 15: 1.00,
    16: 0.95, 17: 0.90, 18: 0.85, 19: 0.80, 20: 0.85,
    21: 0.90, 22: 0.85,
}

# Day of week adjustments
SEND_DAY_FACTORS = {
    0: 0.95,  # Monday
    1: 1.10,  # Tuesday (best)
    2: 1.05,  # Wednesday
    3: 1.08,  # Thursday
    4: 0.90,  # Friday
    5: 0.75,  # Saturday
    6: 0.80,  # Sunday
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class PredictionResult:
    """Campaign performance prediction."""
    campaign_id: str = ""
    channel: str = "email"
    audience_size: int = 0

    # Predicted metrics
    predicted_open_rate: float = 0.0
    predicted_click_rate: float = 0.0
    predicted_conversion_rate: float = 0.0
    predicted_unsubscribe_rate: float = 0.0

    # Confidence intervals (95%)
    open_rate_ci: tuple = (0.0, 0.0)
    click_rate_ci: tuple = (0.0, 0.0)
    conversion_rate_ci: tuple = (0.0, 0.0)

    # Projected outcomes
    estimated_opens: int = 0
    estimated_clicks: int = 0
    estimated_conversions: int = 0

    # ROI projection
    estimated_cost: float = 0.0
    estimated_revenue: float = 0.0
    estimated_roi: float = 0.0

    # Quality scores
    audience_quality_score: float = 0.0
    content_quality_score: float = 0.0
    timing_score: float = 0.0
    overall_score: float = 0.0

    # Recommendations
    recommendations: list = field(default_factory=list)
    optimal_send_time: str = ""

    predicted_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "campaign_id": self.campaign_id,
            "channel": self.channel,
            "audience_size": self.audience_size,
            "predicted_metrics": {
                "open_rate": round(self.predicted_open_rate, 4),
                "click_rate": round(self.predicted_click_rate, 4),
                "conversion_rate": round(self.predicted_conversion_rate, 4),
                "unsubscribe_rate": round(self.predicted_unsubscribe_rate, 4),
            },
            "confidence_intervals": {
                "open_rate": [round(self.open_rate_ci[0], 4), round(self.open_rate_ci[1], 4)],
                "click_rate": [round(self.click_rate_ci[0], 4), round(self.click_rate_ci[1], 4)],
                "conversion_rate": [round(self.conversion_rate_ci[0], 4), round(self.conversion_rate_ci[1], 4)],
            },
            "projected_outcomes": {
                "estimated_opens": self.estimated_opens,
                "estimated_clicks": self.estimated_clicks,
                "estimated_conversions": self.estimated_conversions,
            },
            "roi_projection": {
                "estimated_cost": round(self.estimated_cost, 2),
                "estimated_revenue": round(self.estimated_revenue, 2),
                "estimated_roi": round(self.estimated_roi, 2),
            },
            "quality_scores": {
                "audience_quality": round(self.audience_quality_score, 2),
                "content_quality": round(self.content_quality_score, 2),
                "timing": round(self.timing_score, 2),
                "overall": round(self.overall_score, 2),
            },
            "recommendations": self.recommendations,
            "optimal_send_time": self.optimal_send_time,
            "predicted_at": self.predicted_at,
        }


# ---------------------------------------------------------------------------
# Campaign performance predictor
# ---------------------------------------------------------------------------

class CampaignPredictor:
    """
    Predicts campaign performance using benchmarks, audience analysis,
    content scoring, and historical data.
    """

    def __init__(self):
        self._historical_campaigns: list[dict] = []

    def predict(
        self,
        campaign: dict,
        audience: Optional[list[dict]] = None,
        avg_order_value: float = 50.0,
    ) -> PredictionResult:
        """
        Generate a performance prediction for a campaign.

        Args:
            campaign: Campaign dict with channel, content, schedule, audience_query.
            audience: Optional list of lead dicts for audience analysis.
            avg_order_value: Average order value for revenue estimation.

        Returns:
            PredictionResult with predicted metrics and recommendations.
        """
        channel = campaign.get("channel", "email")
        content = campaign.get("content", {})
        schedule = campaign.get("schedule", {})
        audience_size = len(audience) if audience else campaign.get("audience_size", 1000)

        benchmarks = CHANNEL_BENCHMARKS.get(channel, CHANNEL_BENCHMARKS["email"])

        # 1. Audience quality factor
        audience_factor, audience_score = self._assess_audience_quality(audience)

        # 2. Content quality factor
        content_factor, content_score = self._assess_content_quality(content, channel)

        # 3. Timing factor
        timing_factor, timing_score, optimal_time = self._assess_timing(schedule)

        # 4. Historical adjustment
        historical_factor = self._get_historical_adjustment(channel)

        # Combined multiplier
        combined = audience_factor * content_factor * timing_factor * historical_factor

        # Predict metrics
        open_rate = min(benchmarks.get("open_rate", 0.20) * combined, 0.95)
        click_rate = min(benchmarks.get("click_rate", 0.025) * combined, 0.50)
        conversion_rate = min(benchmarks.get("conversion_rate", 0.012) * combined, 0.30)
        unsub_rate = max(benchmarks.get("unsubscribe_rate", 0.002) / max(combined, 0.5), 0.0001)

        # Confidence intervals (using normal approximation)
        margin = 0.15  # ±15% for 95% CI
        open_ci = (max(0, open_rate * (1 - margin)), min(1, open_rate * (1 + margin)))
        click_ci = (max(0, click_rate * (1 - margin)), min(1, click_rate * (1 + margin)))
        conv_ci = (max(0, conversion_rate * (1 - margin)), min(1, conversion_rate * (1 + margin)))

        # Projected outcomes
        est_opens = int(audience_size * open_rate)
        est_clicks = int(audience_size * click_rate)
        est_conversions = int(audience_size * conversion_rate)

        # Cost estimation
        cost_per = benchmarks.get("cost_per_send", benchmarks.get("cost_per_impression", 0.01))
        est_cost = audience_size * cost_per
        est_revenue = est_conversions * avg_order_value
        est_roi = ((est_revenue - est_cost) / max(est_cost, 0.01)) * 100

        # Overall score (0-100)
        overall_score = (audience_score * 0.35 + content_score * 0.40 + timing_score * 0.25)

        # Recommendations
        recommendations = self._generate_recommendations(
            audience_score, content_score, timing_score,
            open_rate, click_rate, conversion_rate, channel, content
        )

        return PredictionResult(
            campaign_id=campaign.get("id", ""),
            channel=channel,
            audience_size=audience_size,
            predicted_open_rate=open_rate,
            predicted_click_rate=click_rate,
            predicted_conversion_rate=conversion_rate,
            predicted_unsubscribe_rate=unsub_rate,
            open_rate_ci=open_ci,
            click_rate_ci=click_ci,
            conversion_rate_ci=conv_ci,
            estimated_opens=est_opens,
            estimated_clicks=est_clicks,
            estimated_conversions=est_conversions,
            estimated_cost=est_cost,
            estimated_revenue=est_revenue,
            estimated_roi=est_roi,
            audience_quality_score=audience_score,
            content_quality_score=content_score,
            timing_score=timing_score,
            overall_score=overall_score,
            recommendations=recommendations,
            optimal_send_time=optimal_time,
        )

    def record_actual_performance(self, campaign_id: str, channel: str,
                                  actual_metrics: dict) -> None:
        """Record actual campaign performance for model improvement."""
        self._historical_campaigns.append({
            "campaign_id": campaign_id,
            "channel": channel,
            "metrics": actual_metrics,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        })

    # ---- Assessment methods ------------------------------------------------

    def _assess_audience_quality(self, audience: Optional[list[dict]]) -> tuple[float, float]:
        """Assess audience quality and return (factor, score)."""
        if not audience:
            return 1.0, 50.0

        total_score = 0
        for lead in audience:
            lead_score = lead.get("score", 30)
            total_score += lead_score

        avg_score = total_score / len(audience)

        if avg_score >= 60:
            factor = AUDIENCE_QUALITY_FACTORS["engagement_high"]
            quality_score = min(90, 50 + avg_score * 0.5)
        elif avg_score >= 30:
            factor = AUDIENCE_QUALITY_FACTORS["engagement_medium"]
            quality_score = 40 + avg_score * 0.3
        else:
            factor = AUDIENCE_QUALITY_FACTORS["engagement_low"]
            quality_score = max(10, avg_score)

        return factor, quality_score

    def _assess_content_quality(self, content: dict, channel: str) -> tuple[float, float]:
        """Assess content quality and return (factor, score)."""
        factor = 1.0
        score = 50.0
        checks_passed = 0
        total_checks = 7

        subject = str(content.get("subject", ""))
        body = str(content.get("body", ""))
        full_text = f"{subject} {body}".lower()

        # Personalisation
        if "{{" in subject or "{{" in body or content.get("personalised"):
            factor *= CONTENT_FACTORS["personalised"]
            checks_passed += 1

        # Subject length (email-specific)
        if channel == "email" and subject:
            if len(subject) > 60:
                factor *= CONTENT_FACTORS["long_subject"]
            elif len(subject) < 30:
                factor *= CONTENT_FACTORS["short_subject"]
                checks_passed += 1

        # Urgency language
        urgency_words = ["limited", "urgent", "last chance", "expires", "ending soon", "hurry"]
        if any(w in full_text for w in urgency_words):
            factor *= CONTENT_FACTORS["has_urgency"]
            checks_passed += 1

        # Offer/discount
        offer_words = ["discount", "off", "save", "free", "deal", "offer", "coupon"]
        if any(w in full_text for w in offer_words):
            factor *= CONTENT_FACTORS["has_offer"]
            checks_passed += 1

        # Social proof
        proof_words = ["customers", "trusted", "rated", "reviews", "testimonial", "join"]
        if any(w in full_text for w in proof_words):
            factor *= CONTENT_FACTORS["has_social_proof"]
            checks_passed += 1

        # Clear CTA
        cta_words = ["click", "buy", "sign up", "register", "download", "get started", "learn more"]
        if any(w in full_text for w in cta_words):
            factor *= CONTENT_FACTORS["has_clear_cta"]
            checks_passed += 1

        # Mobile optimised
        if content.get("mobile_optimised", False):
            factor *= CONTENT_FACTORS["mobile_optimised"]
            checks_passed += 1

        score = (checks_passed / total_checks) * 100

        return factor, score

    def _assess_timing(self, schedule: dict) -> tuple[float, float, str]:
        """Assess send timing and return (factor, score, optimal_time)."""
        factor = 1.0
        score = 50.0

        send_hour = schedule.get("send_hour")
        send_day = schedule.get("send_day")

        if send_hour is not None:
            hour_factor = SEND_TIME_FACTORS.get(int(send_hour), 0.90)
            factor *= hour_factor
            score = hour_factor * 50

        if send_day is not None:
            day_factor = SEND_DAY_FACTORS.get(int(send_day), 0.95)
            factor *= day_factor
            score = (score + day_factor * 50) / 2

        # Find optimal send time
        best_hour = max(SEND_TIME_FACTORS, key=SEND_TIME_FACTORS.get)
        best_day = max(SEND_DAY_FACTORS, key=SEND_DAY_FACTORS.get)
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        optimal = f"{day_names[best_day]} at {best_hour:02d}:00 UTC"

        return factor, score, optimal

    def _get_historical_adjustment(self, channel: str) -> float:
        """Adjust prediction based on historical performance."""
        channel_history = [
            c for c in self._historical_campaigns if c["channel"] == channel
        ]
        if len(channel_history) < 3:
            return 1.0

        # Compare recent performance to benchmarks
        benchmarks = CHANNEL_BENCHMARKS.get(channel, {})
        recent = channel_history[-5:]

        actual_open_rates = [
            c["metrics"].get("open_rate", benchmarks.get("open_rate", 0.2))
            for c in recent
        ]
        avg_actual = sum(actual_open_rates) / len(actual_open_rates)
        benchmark_open = benchmarks.get("open_rate", 0.2)

        return avg_actual / max(benchmark_open, 0.01)

    # ---- Recommendations ---------------------------------------------------

    def _generate_recommendations(
        self, audience_score: float, content_score: float,
        timing_score: float, open_rate: float, click_rate: float,
        conversion_rate: float, channel: str, content: dict,
    ) -> list[dict]:
        """Generate actionable recommendations to improve performance."""
        recs = []

        if audience_score < 40:
            recs.append({
                "category": "audience",
                "priority": "high",
                "recommendation": "Improve audience targeting – consider using a more engaged segment",
                "expected_impact": "+15-25% improvement in engagement metrics",
            })

        if content_score < 40:
            recs.append({
                "category": "content",
                "priority": "high",
                "recommendation": "Add personalisation tokens (name, company) to subject and body",
                "expected_impact": "+26% open rate improvement",
            })

        subject = str(content.get("subject", ""))
        if channel == "email" and len(subject) > 60:
            recs.append({
                "category": "content",
                "priority": "medium",
                "recommendation": "Shorten email subject line to under 50 characters",
                "expected_impact": "+10% open rate improvement",
            })

        if not content.get("mobile_optimised"):
            recs.append({
                "category": "content",
                "priority": "medium",
                "recommendation": "Ensure content is mobile-optimised (60%+ of opens are mobile)",
                "expected_impact": "+10% engagement improvement",
            })

        if timing_score < 50:
            recs.append({
                "category": "timing",
                "priority": "medium",
                "recommendation": "Consider sending on Tuesday-Thursday between 9-11 AM UTC",
                "expected_impact": "+10-20% open rate improvement",
            })

        body = str(content.get("body", "")).lower()
        cta_words = ["click", "buy", "sign up", "register", "download", "get started"]
        if not any(w in body for w in cta_words):
            recs.append({
                "category": "content",
                "priority": "high",
                "recommendation": "Add a clear call-to-action (CTA) to drive clicks",
                "expected_impact": "+18% click-through rate improvement",
            })

        if open_rate < 0.15:
            recs.append({
                "category": "deliverability",
                "priority": "high",
                "recommendation": "Review sender reputation and list hygiene – low predicted open rate",
                "expected_impact": "Improved inbox placement",
            })

        if conversion_rate < 0.005:
            recs.append({
                "category": "conversion",
                "priority": "medium",
                "recommendation": "Optimise landing page and reduce friction in conversion funnel",
                "expected_impact": "+20-50% conversion improvement",
            })

        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recs.sort(key=lambda r: priority_order.get(r["priority"], 2))

        return recs

    def get_channel_benchmarks(self, channel: Optional[str] = None) -> dict:
        """Return industry benchmarks for one or all channels."""
        if channel:
            return CHANNEL_BENCHMARKS.get(channel, {})
        return CHANNEL_BENCHMARKS
