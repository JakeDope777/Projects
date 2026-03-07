"""
KPI Engine — 30+ Marketing Metrics across the AARRR Framework

Covers Acquisition, Activation, Retention, Revenue, and Referral stages
with computed metrics derived from raw data inputs.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------

@dataclass
class RawMetricsInput:
    """Raw data fed into the KPI engine from integrations / data ingestion."""

    # Traffic & Acquisition
    impressions: int = 0
    clicks: int = 0
    sessions: int = 0
    unique_visitors: int = 0
    new_visitors: int = 0
    returning_visitors: int = 0
    organic_sessions: int = 0
    paid_sessions: int = 0
    social_sessions: int = 0
    referral_sessions: int = 0
    direct_sessions: int = 0

    # Spend
    total_ad_spend: float = 0.0
    total_marketing_spend: float = 0.0

    # Leads & Activation
    total_leads: int = 0
    new_leads: int = 0
    marketing_qualified_leads: int = 0
    sales_qualified_leads: int = 0
    signups: int = 0
    activations: int = 0  # users who completed key action
    trial_starts: int = 0
    onboarding_completions: int = 0

    # Conversions
    conversions: int = 0
    purchases: int = 0
    demo_requests: int = 0

    # Revenue
    total_revenue: float = 0.0
    new_revenue: float = 0.0
    expansion_revenue: float = 0.0
    churned_revenue: float = 0.0
    total_customers: int = 0
    new_customers: int = 0
    churned_customers: int = 0

    # Retention
    active_users_start: int = 0
    active_users_end: int = 0
    returning_customers: int = 0
    support_tickets: int = 0
    nps_responses: list[int] = field(default_factory=list)

    # Email
    emails_sent: int = 0
    emails_delivered: int = 0
    emails_opened: int = 0
    emails_clicked: int = 0
    emails_bounced: int = 0
    emails_unsubscribed: int = 0

    # Referral
    referral_invites_sent: int = 0
    referral_invites_accepted: int = 0
    referral_conversions: int = 0

    # Content / Engagement
    page_views: int = 0
    avg_session_duration_seconds: float = 0.0
    bounce_rate_raw: float = 0.0  # 0-100
    pages_per_session: float = 0.0

    # Customer lifetime
    avg_customer_lifespan_months: float = 12.0
    avg_revenue_per_customer_monthly: float = 0.0

    # Time period (days)
    period_days: int = 30


# ---------------------------------------------------------------------------
# KPI definitions
# ---------------------------------------------------------------------------

KPI_CATALOG: list[dict[str, str]] = [
    # ── Acquisition ──
    {"id": "impressions", "name": "Impressions", "stage": "acquisition", "unit": "count"},
    {"id": "clicks", "name": "Clicks", "stage": "acquisition", "unit": "count"},
    {"id": "ctr", "name": "Click-Through Rate", "stage": "acquisition", "unit": "%"},
    {"id": "cpc", "name": "Cost per Click", "stage": "acquisition", "unit": "$"},
    {"id": "cpm", "name": "Cost per Mille (1k Impressions)", "stage": "acquisition", "unit": "$"},
    {"id": "sessions", "name": "Sessions", "stage": "acquisition", "unit": "count"},
    {"id": "unique_visitors", "name": "Unique Visitors", "stage": "acquisition", "unit": "count"},
    {"id": "new_visitor_ratio", "name": "New Visitor Ratio", "stage": "acquisition", "unit": "%"},
    {"id": "traffic_channel_mix", "name": "Traffic Channel Mix", "stage": "acquisition", "unit": "dict"},
    {"id": "cost_per_lead", "name": "Cost per Lead (CPL)", "stage": "acquisition", "unit": "$"},
    {"id": "cac", "name": "Customer Acquisition Cost", "stage": "acquisition", "unit": "$"},

    # ── Activation ──
    {"id": "signup_rate", "name": "Signup Rate", "stage": "activation", "unit": "%"},
    {"id": "activation_rate", "name": "Activation Rate", "stage": "activation", "unit": "%"},
    {"id": "onboarding_completion_rate", "name": "Onboarding Completion Rate", "stage": "activation", "unit": "%"},
    {"id": "lead_to_mql_rate", "name": "Lead → MQL Conversion", "stage": "activation", "unit": "%"},
    {"id": "mql_to_sql_rate", "name": "MQL → SQL Conversion", "stage": "activation", "unit": "%"},
    {"id": "demo_request_rate", "name": "Demo Request Rate", "stage": "activation", "unit": "%"},
    {"id": "trial_start_rate", "name": "Trial Start Rate", "stage": "activation", "unit": "%"},

    # ── Retention ──
    {"id": "retention_rate", "name": "Customer Retention Rate", "stage": "retention", "unit": "%"},
    {"id": "churn_rate", "name": "Churn Rate", "stage": "retention", "unit": "%"},
    {"id": "net_promoter_score", "name": "Net Promoter Score (NPS)", "stage": "retention", "unit": "score"},
    {"id": "bounce_rate", "name": "Bounce Rate", "stage": "retention", "unit": "%"},
    {"id": "avg_session_duration", "name": "Avg Session Duration", "stage": "retention", "unit": "seconds"},
    {"id": "pages_per_session", "name": "Pages per Session", "stage": "retention", "unit": "count"},

    # ── Revenue ──
    {"id": "total_revenue", "name": "Total Revenue", "stage": "revenue", "unit": "$"},
    {"id": "mrr", "name": "Monthly Recurring Revenue", "stage": "revenue", "unit": "$"},
    {"id": "arpu", "name": "Avg Revenue per User", "stage": "revenue", "unit": "$"},
    {"id": "ltv", "name": "Customer Lifetime Value", "stage": "revenue", "unit": "$"},
    {"id": "ltv_cac_ratio", "name": "LTV:CAC Ratio", "stage": "revenue", "unit": "ratio"},
    {"id": "roas", "name": "Return on Ad Spend", "stage": "revenue", "unit": "ratio"},
    {"id": "conversion_rate", "name": "Conversion Rate", "stage": "revenue", "unit": "%"},
    {"id": "net_revenue_retention", "name": "Net Revenue Retention", "stage": "revenue", "unit": "%"},

    # ── Referral ──
    {"id": "referral_rate", "name": "Referral Rate", "stage": "referral", "unit": "%"},
    {"id": "viral_coefficient", "name": "Viral Coefficient (K-factor)", "stage": "referral", "unit": "ratio"},
    {"id": "referral_conversion_rate", "name": "Referral Conversion Rate", "stage": "referral", "unit": "%"},

    # ── Email ──
    {"id": "email_open_rate", "name": "Email Open Rate", "stage": "activation", "unit": "%"},
    {"id": "email_click_rate", "name": "Email Click Rate", "stage": "activation", "unit": "%"},
    {"id": "email_bounce_rate", "name": "Email Bounce Rate", "stage": "activation", "unit": "%"},
    {"id": "email_unsubscribe_rate", "name": "Email Unsubscribe Rate", "stage": "retention", "unit": "%"},
]


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

def _safe_div(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Division that returns *default* when denominator is zero."""
    return (numerator / denominator) if denominator else default


def _pct(numerator: float, denominator: float) -> float:
    return round(_safe_div(numerator * 100, denominator), 2)


class KPIEngine:
    """Compute 30+ marketing KPIs from raw metric inputs."""

    CATALOG = KPI_CATALOG

    def compute_all(self, raw: RawMetricsInput) -> dict[str, Any]:
        """Return a flat dict of all computed KPIs."""
        m: dict[str, Any] = {}

        # ── Acquisition ──────────────────────────────────────────────
        m["impressions"] = raw.impressions
        m["clicks"] = raw.clicks
        m["ctr"] = _pct(raw.clicks, raw.impressions)
        m["cpc"] = round(_safe_div(raw.total_ad_spend, raw.clicks), 2)
        m["cpm"] = round(_safe_div(raw.total_ad_spend * 1000, raw.impressions), 2)
        m["sessions"] = raw.sessions
        m["unique_visitors"] = raw.unique_visitors
        m["new_visitor_ratio"] = _pct(raw.new_visitors, raw.unique_visitors)
        m["traffic_channel_mix"] = {
            "organic": raw.organic_sessions,
            "paid": raw.paid_sessions,
            "social": raw.social_sessions,
            "referral": raw.referral_sessions,
            "direct": raw.direct_sessions,
        }
        m["cost_per_lead"] = round(_safe_div(raw.total_marketing_spend, raw.new_leads), 2)
        m["cac"] = round(_safe_div(raw.total_marketing_spend, raw.new_customers), 2)

        # ── Activation ───────────────────────────────────────────────
        m["signup_rate"] = _pct(raw.signups, raw.sessions)
        m["activation_rate"] = _pct(raw.activations, raw.signups)
        m["onboarding_completion_rate"] = _pct(raw.onboarding_completions, raw.signups)
        m["lead_to_mql_rate"] = _pct(raw.marketing_qualified_leads, raw.total_leads)
        m["mql_to_sql_rate"] = _pct(raw.sales_qualified_leads, raw.marketing_qualified_leads)
        m["demo_request_rate"] = _pct(raw.demo_requests, raw.sessions)
        m["trial_start_rate"] = _pct(raw.trial_starts, raw.signups)

        # ── Retention ────────────────────────────────────────────────
        retained = raw.total_customers - raw.churned_customers
        m["retention_rate"] = _pct(retained, raw.total_customers)
        m["churn_rate"] = _pct(raw.churned_customers, raw.total_customers)
        m["net_promoter_score"] = self._compute_nps(raw.nps_responses)
        m["bounce_rate"] = round(raw.bounce_rate_raw, 2)
        m["avg_session_duration"] = round(raw.avg_session_duration_seconds, 1)
        m["pages_per_session"] = round(raw.pages_per_session, 2)

        # ── Revenue ──────────────────────────────────────────────────
        m["total_revenue"] = round(raw.total_revenue, 2)
        m["mrr"] = round(
            _safe_div(raw.total_revenue, max(raw.period_days / 30, 1)), 2
        )
        m["arpu"] = round(_safe_div(raw.total_revenue, raw.total_customers), 2)
        m["ltv"] = round(
            raw.avg_revenue_per_customer_monthly * raw.avg_customer_lifespan_months, 2
        )
        m["ltv_cac_ratio"] = round(
            _safe_div(m["ltv"], m["cac"]), 2
        )
        m["roas"] = round(_safe_div(raw.total_revenue, raw.total_ad_spend), 2)
        m["conversion_rate"] = _pct(raw.conversions, raw.sessions)
        prev_revenue = raw.total_revenue - raw.new_revenue
        m["net_revenue_retention"] = _pct(
            prev_revenue + raw.expansion_revenue - raw.churned_revenue,
            prev_revenue,
        ) if prev_revenue else 0.0

        # ── Referral ─────────────────────────────────────────────────
        m["referral_rate"] = _pct(raw.referral_invites_sent, raw.total_customers)
        m["viral_coefficient"] = round(
            _safe_div(raw.referral_invites_sent, raw.total_customers)
            * _safe_div(raw.referral_invites_accepted, raw.referral_invites_sent),
            3,
        )
        m["referral_conversion_rate"] = _pct(
            raw.referral_conversions, raw.referral_invites_accepted
        )

        # ── Email ────────────────────────────────────────────────────
        m["email_open_rate"] = _pct(raw.emails_opened, raw.emails_delivered)
        m["email_click_rate"] = _pct(raw.emails_clicked, raw.emails_delivered)
        m["email_bounce_rate"] = _pct(raw.emails_bounced, raw.emails_sent)
        m["email_unsubscribe_rate"] = _pct(raw.emails_unsubscribed, raw.emails_delivered)

        return m

    def compute_stage(self, raw: RawMetricsInput, stage: str) -> dict[str, Any]:
        """Return only KPIs belonging to a specific AARRR stage."""
        all_kpis = self.compute_all(raw)
        stage_ids = {k["id"] for k in KPI_CATALOG if k["stage"] == stage}
        return {k: v for k, v in all_kpis.items() if k in stage_ids}

    def get_catalog(self) -> list[dict[str, str]]:
        """Return the full KPI catalog with metadata."""
        return list(KPI_CATALOG)

    # ------------------------------------------------------------------
    @staticmethod
    def _compute_nps(responses: list[int]) -> float:
        """Compute Net Promoter Score from a list of 0-10 ratings."""
        if not responses:
            return 0.0
        promoters = sum(1 for r in responses if r >= 9)
        detractors = sum(1 for r in responses if r <= 6)
        total = len(responses)
        return round(((promoters - detractors) / total) * 100, 1)
