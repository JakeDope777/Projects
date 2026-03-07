"""
Intent Router - classifies user intent and routes to the appropriate skill module.

Supports three classification strategies (applied in cascade):
1. **Few-shot embedding classification** – computes cosine similarity between the
   user query embedding and a curated set of exemplar embeddings for each skill.
2. **Keyword / regex matching** – fast, deterministic fallback.
3. **LLM-based classification** – used when the first two methods are ambiguous.

The router is designed to be initialised once and reused across requests.
"""

from __future__ import annotations

import re
import math
import hashlib
import json
import os
from typing import Optional, Any

# ---------------------------------------------------------------------------
# Skill module identifiers
# ---------------------------------------------------------------------------
SKILL_BUSINESS_ANALYSIS = "business_analysis"
SKILL_CREATIVE_DESIGN = "creative_design"
SKILL_CRM_CAMPAIGN = "crm_campaign"
SKILL_ANALYTICS_REPORTING = "analytics_reporting"
SKILL_INTEGRATIONS = "integrations"
SKILL_SYSTEM = "system"
SKILL_GENERAL = "general"

ALL_SKILLS = [
    SKILL_BUSINESS_ANALYSIS,
    SKILL_CREATIVE_DESIGN,
    SKILL_CRM_CAMPAIGN,
    SKILL_ANALYTICS_REPORTING,
    SKILL_INTEGRATIONS,
    SKILL_SYSTEM,
    SKILL_GENERAL,
]

# ---------------------------------------------------------------------------
# Few-shot exemplars for embedding-based classification
# ---------------------------------------------------------------------------
SKILL_EXEMPLARS: dict[str, list[str]] = {
    SKILL_BUSINESS_ANALYSIS: [
        "Do a SWOT analysis for our product",
        "Research our competitor landscape",
        "Create buyer personas for our target audience",
        "What is the market size for SaaS in Europe?",
        "Perform a PESTEL analysis for our industry",
        "Identify key market trends in fintech",
        "Segment our customer base by demographics",
        "Analyse the competitive positioning of our brand",
        "What are the barriers to entry in this market?",
        "Summarise the industry outlook for 2025",
    ],
    SKILL_CREATIVE_DESIGN: [
        "Write a blog post about our new feature",
        "Generate a banner image for our campaign",
        "Suggest A/B test variations for this headline",
        "Create social media captions for Instagram",
        "Draft an email subject line for our newsletter",
        "Build a content calendar for Q2",
        "Write ad copy for Google Ads",
        "Design a brand voice guideline document",
        "Generate creative ideas for a product launch",
        "Rewrite this paragraph in a more engaging tone",
    ],
    SKILL_CRM_CAMPAIGN: [
        "Update the lead status in our CRM",
        "Create an email campaign for new users",
        "Check GDPR compliance for this message",
        "Set up a drip campaign for onboarding",
        "Import contacts from a CSV into HubSpot",
        "Build an email nurture sequence for leads",
        "Segment our audience for the holiday campaign",
        "Send a follow-up email to trial users",
        "Create a workflow to score inbound leads",
        "How do I comply with CAN-SPAM regulations?",
    ],
    SKILL_ANALYTICS_REPORTING: [
        "Show me the analytics dashboard",
        "What is our current CAC and LTV?",
        "Forecast our conversion rate for next month",
        "Generate a weekly performance report",
        "What was our ROAS last quarter?",
        "Compare CTR across our ad campaigns",
        "Visualise our funnel drop-off rates",
        "Track impressions and clicks for the past week",
        "Calculate the ROI of our latest campaign",
        "Build a KPI dashboard for the marketing team",
    ],
    SKILL_INTEGRATIONS: [
        "Connect our Google Ads account via OAuth",
        "Set up the HubSpot integration",
        "Configure a webhook for Stripe events",
        "Sync our LinkedIn Ads data",
        "How do I connect the SendGrid API?",
        "Integrate Google Analytics with our dashboard",
        "Set up the Meta Ads connector",
        "Test the API connection to our CRM",
        "Enable two-way sync with Salesforce",
        "Install the Slack notification integration",
    ],
    SKILL_SYSTEM: [
        "Change my account settings and preferences",
        "Update my password",
        "How many tokens have I used this month?",
        "Remember that I prefer formal tone",
        "Forget my previous brand guidelines",
        "Show my subscription details",
        "Update my profile information",
        "What are my current memory settings?",
        "Clear my conversation history",
        "Set my default project to 'Alpha'",
    ],
    SKILL_GENERAL: [
        "Hello, how are you today?",
        "Tell me something interesting",
        "What can you do?",
        "Thanks for your help",
        "Good morning",
        "Can you explain how you work?",
        "Who built you?",
        "I need some help",
        "What is marketing?",
        "Give me a fun fact",
    ],
}

# ---------------------------------------------------------------------------
# Keyword patterns (deterministic fallback)
# ---------------------------------------------------------------------------
INTENT_PATTERNS: dict[str, list[str]] = {
    SKILL_BUSINESS_ANALYSIS: [
        r"\b(market\s*research|competitor|swot|pestel|persona|industry|trend|"
        r"competitive\s*analysis|market\s*size|target\s*audience|segmentation)\b",
    ],
    SKILL_CREATIVE_DESIGN: [
        r"\b(write|copy|blog\s*post|headline|caption|email\s*subject|"
        r"content\s*calendar|a/?b\s*test|generate\s*image|banner|"
        r"creative|design|brand\s*voice|social\s*media\s*post|ad\s*copy)\b",
    ],
    SKILL_CRM_CAMPAIGN: [
        r"\b(lead|crm|campaign|workflow|email\s*sequence|hubspot|salesforce|"
        r"compliance|gdpr|can.spam|nurture|drip|audience|send\s*email)\b",
    ],
    SKILL_ANALYTICS_REPORTING: [
        r"\b(analytics|dashboard|metric|kpi|cac|ltv|roi|roas|ctr|"
        r"conversion\s*rate|forecast|report|chart|experiment|"
        r"performance|spend|impressions|clicks)\b",
    ],
    SKILL_INTEGRATIONS: [
        r"\b(connect|integration|api|oauth|google\s*ads|meta\s*ads|"
        r"sendgrid|linkedin|webhook|sync|connector)\b",
    ],
    SKILL_SYSTEM: [
        r"\b(settings|account|subscription|token|usage|password|"
        r"profile|preference|memory|remember|forget)\b",
    ],
}

# ---------------------------------------------------------------------------
# Lightweight embedding helpers (no heavy ML model required at import time)
# ---------------------------------------------------------------------------

def _simple_tokenize(text: str) -> list[str]:
    """Lowercase split + basic punctuation removal."""
    return re.findall(r"[a-z0-9]+", text.lower())


def _term_frequency(tokens: list[str]) -> dict[str, float]:
    freq: dict[str, int] = {}
    for t in tokens:
        freq[t] = freq.get(t, 0) + 1
    total = len(tokens) or 1
    return {t: c / total for t, c in freq.items()}


def _cosine_similarity(a: dict[str, float], b: dict[str, float]) -> float:
    """Cosine similarity between two sparse TF vectors."""
    common = set(a) & set(b)
    if not common:
        return 0.0
    dot = sum(a[k] * b[k] for k in common)
    mag_a = math.sqrt(sum(v * v for v in a.values()))
    mag_b = math.sqrt(sum(v * v for v in b.values()))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


class IntentRouter:
    """
    Multi-strategy intent classifier.

    Classification cascade:
    1. Embedding similarity against few-shot exemplars (if available).
    2. Regex keyword matching (deterministic fallback).
    3. LLM classification (async, for truly ambiguous queries).

    The router pre-computes TF vectors for all exemplars at init time so that
    classification is fast at request time.  When an external embedding function
    is provided (e.g. OpenAI ``text-embedding-ada-002``), it is used instead of
    the built-in TF vectors for higher accuracy.
    """

    # Confidence thresholds
    EMBEDDING_CONFIDENCE_THRESHOLD = 0.35
    KEYWORD_CONFIDENCE_THRESHOLD = 1  # minimum keyword hits

    def __init__(
        self,
        llm_client: Any = None,
        embedding_fn: Optional[Any] = None,
    ):
        """
        Args:
            llm_client: Optional async LLM client with a ``generate`` method.
            embedding_fn: Optional callable ``(text: str) -> list[float]`` that
                returns a dense embedding vector.  When provided, dense cosine
                similarity is used instead of sparse TF matching.
        """
        self.llm_client = llm_client
        self.embedding_fn = embedding_fn

        # Pre-compile regex patterns
        self._compiled_patterns: dict[str, list[re.Pattern]] = {}
        for skill, patterns in INTENT_PATTERNS.items():
            self._compiled_patterns[skill] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]

        # Pre-compute sparse TF vectors for exemplars
        self._exemplar_tf: dict[str, list[dict[str, float]]] = {}
        for skill, examples in SKILL_EXEMPLARS.items():
            self._exemplar_tf[skill] = [
                _term_frequency(_simple_tokenize(ex)) for ex in examples
            ]

        # Dense exemplar cache (populated lazily when embedding_fn is set)
        self._exemplar_dense: dict[str, list[list[float]]] = {}

    # ------------------------------------------------------------------
    # Dense embedding helpers
    # ------------------------------------------------------------------

    def _ensure_dense_exemplars(self) -> None:
        """Compute dense embeddings for all exemplars (once)."""
        if self._exemplar_dense or self.embedding_fn is None:
            return
        for skill, examples in SKILL_EXEMPLARS.items():
            self._exemplar_dense[skill] = [
                self.embedding_fn(ex) for ex in examples
            ]

    @staticmethod
    def _dense_cosine(a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        mag_a = math.sqrt(sum(x * x for x in a))
        mag_b = math.sqrt(sum(x * x for x in b))
        if mag_a == 0 or mag_b == 0:
            return 0.0
        return dot / (mag_a * mag_b)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def classify_intent(self, message: str) -> str:
        """
        Synchronous intent classification using the embedding + keyword cascade.

        Returns the best-matching skill identifier.
        """
        result = self.classify_with_confidence(message)
        return result["skill"]

    def classify_with_confidence(self, message: str) -> dict:
        """
        Classify and return ``{"skill": str, "confidence": float, "method": str}``.
        """
        # Strategy 1: Dense embedding similarity (if available)
        if self.embedding_fn is not None:
            self._ensure_dense_exemplars()
            query_vec = self.embedding_fn(message)
            best_skill = SKILL_GENERAL
            best_score = 0.0
            for skill, vecs in self._exemplar_dense.items():
                for vec in vecs:
                    sim = self._dense_cosine(query_vec, vec)
                    if sim > best_score:
                        best_score = sim
                        best_skill = skill
            if best_score >= self.EMBEDDING_CONFIDENCE_THRESHOLD:
                return {"skill": best_skill, "confidence": best_score, "method": "dense_embedding"}

        # Strategy 2: Sparse TF similarity against exemplars
        query_tf = _term_frequency(_simple_tokenize(message))
        best_skill = SKILL_GENERAL
        best_score = 0.0
        for skill, tf_list in self._exemplar_tf.items():
            for tf_vec in tf_list:
                sim = _cosine_similarity(query_tf, tf_vec)
                if sim > best_score:
                    best_score = sim
                    best_skill = skill

        if best_score >= self.EMBEDDING_CONFIDENCE_THRESHOLD:
            return {"skill": best_skill, "confidence": best_score, "method": "sparse_embedding"}

        # Strategy 3: Keyword / regex matching
        keyword_result = self._keyword_classify(message)
        if keyword_result["confidence"] >= self.KEYWORD_CONFIDENCE_THRESHOLD:
            return keyword_result

        # If sparse embedding had *any* signal, prefer it over GENERAL
        if best_score > 0:
            return {"skill": best_skill, "confidence": best_score, "method": "sparse_embedding_low"}

        return {"skill": SKILL_GENERAL, "confidence": 0.0, "method": "default"}

    def _keyword_classify(self, message: str) -> dict:
        """Regex keyword classification with score."""
        scores: dict[str, int] = {skill: 0 for skill in INTENT_PATTERNS}
        for skill, compiled in self._compiled_patterns.items():
            for pattern in compiled:
                matches = pattern.findall(message)
                scores[skill] += len(matches)

        max_score = max(scores.values())
        if max_score == 0:
            return {"skill": SKILL_GENERAL, "confidence": 0, "method": "keyword"}

        best_skill = max(scores, key=scores.get)  # type: ignore[arg-type]
        return {"skill": best_skill, "confidence": max_score, "method": "keyword"}

    async def classify_with_llm(self, message: str) -> str:
        """
        Use an LLM to classify ambiguous intents.  Falls back to the
        synchronous cascade if the LLM client is unavailable.
        """
        if self.llm_client is None:
            return self.classify_intent(message)

        try:
            prompt = (
                "You are an intent classifier for a marketing AI assistant.\n"
                "Classify the following user message into exactly ONE of these categories:\n"
                "  business_analysis, creative_design, crm_campaign, "
                "analytics_reporting, integrations, system, general\n\n"
                "Few-shot examples:\n"
                '  "Do a SWOT analysis" → business_analysis\n'
                '  "Write a blog post" → creative_design\n'
                '  "Set up a drip campaign" → crm_campaign\n'
                '  "Show me the dashboard" → analytics_reporting\n'
                '  "Connect Google Ads" → integrations\n'
                '  "Change my password" → system\n'
                '  "Hello" → general\n\n'
                f'User message: "{message}"\n\n'
                "Respond with ONLY the category name, nothing else."
            )
            # LLM client may accept a string or list of dicts
            if hasattr(self.llm_client, "generate"):
                response = await self.llm_client.generate(prompt)
            else:
                response = str(self.llm_client)
            category = response.strip().lower().replace(" ", "_")
            if category in ALL_SKILLS:
                return category
            return self.classify_intent(message)
        except Exception:
            return self.classify_intent(message)

    def get_available_skills(self) -> list[str]:
        """Return a list of all registered skill identifiers."""
        return list(ALL_SKILLS)

    def get_skill_exemplars(self, skill: str) -> list[str]:
        """Return the few-shot exemplars for a given skill."""
        return list(SKILL_EXEMPLARS.get(skill, []))
