"""
SWOT & PESTEL Analysis Engine

Provides enhanced, data-enriched SWOT and PESTEL analysis generation
with structured output, scoring, confidence levels, and integration
with real data sources for evidence-backed strategic insights.
"""

import json
import logging
from datetime import datetime
from typing import Optional, Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Structured output schemas
# ---------------------------------------------------------------------------

SWOT_ITEM_SCHEMA = {
    "factor": "string — concise description of the factor",
    "impact": "high | medium | low",
    "confidence": "high | medium | low — how confident is this assessment",
    "evidence": "string — supporting data or reasoning",
    "recommendations": "list[string] — actionable recommendations",
}

PESTEL_ITEM_SCHEMA = {
    "factor": "string — concise description",
    "impact": "high | medium | low",
    "likelihood": "high | medium | low — probability of occurrence",
    "timeframe": "short-term | medium-term | long-term",
    "evidence": "string — supporting data or reasoning",
    "implications": "list[string] — business implications",
}


# ---------------------------------------------------------------------------
# Enhanced prompt templates
# ---------------------------------------------------------------------------

ENHANCED_SWOT_TEMPLATE = """You are a senior business strategy consultant. Perform a comprehensive SWOT analysis for:

**Subject:** {subject}
**Industry:** {industry}
**Context:** {context}

{data_context}

{domain_factors}

Provide a rigorous, data-driven SWOT analysis. For EACH factor, include:
1. A concise description of the factor
2. Impact level (high / medium / low)
3. Confidence level (high / medium / low)
4. Supporting evidence or data
5. Actionable recommendations

Return your analysis as a JSON object with this EXACT structure:
{{
    "subject": "{subject}",
    "industry": "{industry}",
    "generated_at": "<ISO timestamp>",
    "summary": "<2-3 sentence executive summary>",
    "strengths": [
        {{
            "factor": "<description>",
            "impact": "high|medium|low",
            "confidence": "high|medium|low",
            "evidence": "<supporting data>",
            "recommendations": ["<action 1>", "<action 2>"]
        }}
    ],
    "weaknesses": [
        {{
            "factor": "<description>",
            "impact": "high|medium|low",
            "confidence": "high|medium|low",
            "evidence": "<supporting data>",
            "recommendations": ["<action 1>", "<action 2>"]
        }}
    ],
    "opportunities": [
        {{
            "factor": "<description>",
            "impact": "high|medium|low",
            "confidence": "high|medium|low",
            "evidence": "<supporting data>",
            "recommendations": ["<action 1>", "<action 2>"]
        }}
    ],
    "threats": [
        {{
            "factor": "<description>",
            "impact": "high|medium|low",
            "confidence": "high|medium|low",
            "evidence": "<supporting data>",
            "recommendations": ["<action 1>", "<action 2>"]
        }}
    ],
    "cross_analysis": {{
        "so_strategies": ["<leverage strength to capture opportunity>"],
        "wo_strategies": ["<overcome weakness to capture opportunity>"],
        "st_strategies": ["<use strength to mitigate threat>"],
        "wt_strategies": ["<minimise weakness and avoid threat>"]
    }},
    "priority_actions": ["<top 3-5 priority actions>"]
}}

Provide at least 3 items per SWOT category. Be specific and actionable.
Return ONLY valid JSON, no markdown formatting.
"""

ENHANCED_PESTEL_TEMPLATE = """You are a senior business strategy consultant. Perform a comprehensive PESTEL analysis for:

**Subject:** {subject}
**Industry:** {industry}
**Context:** {context}

{data_context}

{domain_factors}

For EACH factor, include:
1. A concise description
2. Impact level (high / medium / low)
3. Likelihood of occurrence (high / medium / low)
4. Timeframe (short-term / medium-term / long-term)
5. Supporting evidence
6. Business implications

Return your analysis as a JSON object with this EXACT structure:
{{
    "subject": "{subject}",
    "industry": "{industry}",
    "generated_at": "<ISO timestamp>",
    "summary": "<2-3 sentence executive summary>",
    "political": [
        {{
            "factor": "<description>",
            "impact": "high|medium|low",
            "likelihood": "high|medium|low",
            "timeframe": "short-term|medium-term|long-term",
            "evidence": "<supporting data>",
            "implications": ["<implication 1>", "<implication 2>"]
        }}
    ],
    "economic": [<same structure>],
    "social": [<same structure>],
    "technological": [<same structure>],
    "environmental": [<same structure>],
    "legal": [<same structure>],
    "risk_matrix": {{
        "high_impact_high_likelihood": ["<factor descriptions>"],
        "high_impact_low_likelihood": ["<factor descriptions>"],
        "low_impact_high_likelihood": ["<factor descriptions>"],
        "low_impact_low_likelihood": ["<factor descriptions>"]
    }},
    "strategic_recommendations": ["<top 5 recommendations>"]
}}

Provide at least 2 items per PESTEL category. Be specific and evidence-based.
Return ONLY valid JSON, no markdown formatting.
"""


class SWOTPESTELAnalyzer:
    """
    Enhanced SWOT and PESTEL analysis generator with data enrichment,
    structured output, and cross-analysis capabilities.
    """

    def __init__(
        self,
        llm_client=None,
        news_client=None,
        trends_client=None,
        wikipedia_client=None,
        web_scraper=None,
    ):
        self.llm = llm_client
        self.news_client = news_client
        self.trends_client = trends_client
        self.wikipedia_client = wikipedia_client
        self.web_scraper = web_scraper

    async def generate_swot(
        self,
        subject: str,
        industry: str = "",
        context: Optional[dict] = None,
        domain_profile: Optional[dict] = None,
        enrich_with_data: bool = True,
    ) -> dict:
        """
        Generate a comprehensive SWOT analysis with optional data enrichment.

        Args:
            subject: The company, product, or topic to analyse.
            industry: Industry context.
            context: Additional context dict.
            domain_profile: Pre-configured domain profile with industry factors.
            enrich_with_data: Whether to fetch real data for enrichment.

        Returns:
            Structured SWOT analysis dict.
        """
        context = context or {}
        data_context = ""
        domain_factors = ""

        if enrich_with_data:
            data_context = await self._gather_data_context(subject, industry)

        if domain_profile:
            swot_factors = domain_profile.get("swot_factors", {})
            if swot_factors:
                domain_factors = (
                    "Consider these industry-specific factors in your analysis:\n"
                    f"- Typical Strengths: {', '.join(swot_factors.get('typical_strengths', []))}\n"
                    f"- Typical Weaknesses: {', '.join(swot_factors.get('typical_weaknesses', []))}\n"
                    f"- Common Opportunities: {', '.join(swot_factors.get('common_opportunities', []))}\n"
                    f"- Known Threats: {', '.join(swot_factors.get('known_threats', []))}\n"
                )

        prompt = ENHANCED_SWOT_TEMPLATE.format(
            subject=subject,
            industry=industry or "General",
            context=json.dumps(context, default=str),
            data_context=data_context,
            domain_factors=domain_factors,
        )

        raw_response = await self._call_llm(prompt)
        analysis = self._parse_json_response(raw_response)

        if not analysis:
            analysis = self._build_fallback_swot(subject, industry)

        analysis["metadata"] = {
            "subject": subject,
            "industry": industry,
            "data_enriched": enrich_with_data,
            "domain_profile_used": domain_profile is not None,
            "generated_at": datetime.utcnow().isoformat(),
            "model": "llm" if self.llm else "demo",
        }

        return {
            "analysis": analysis,
            "type": "swot",
            "insights": self._extract_insights(analysis, "swot"),
        }

    async def generate_pestel(
        self,
        subject: str,
        industry: str = "",
        context: Optional[dict] = None,
        domain_profile: Optional[dict] = None,
        enrich_with_data: bool = True,
    ) -> dict:
        """
        Generate a comprehensive PESTEL analysis with optional data enrichment.

        Args:
            subject: The company, product, or topic to analyse.
            industry: Industry context.
            context: Additional context dict.
            domain_profile: Pre-configured domain profile.
            enrich_with_data: Whether to fetch real data for enrichment.

        Returns:
            Structured PESTEL analysis dict.
        """
        context = context or {}
        data_context = ""
        domain_factors = ""

        if enrich_with_data:
            data_context = await self._gather_data_context(subject, industry)

        if domain_profile:
            pestel_factors = domain_profile.get("pestel_factors", {})
            if pestel_factors:
                lines = ["Consider these industry-specific PESTEL factors:"]
                for category, factors in pestel_factors.items():
                    if factors:
                        lines.append(f"- {category.title()}: {', '.join(factors)}")
                domain_factors = "\n".join(lines)

        prompt = ENHANCED_PESTEL_TEMPLATE.format(
            subject=subject,
            industry=industry or "General",
            context=json.dumps(context, default=str),
            data_context=data_context,
            domain_factors=domain_factors,
        )

        raw_response = await self._call_llm(prompt)
        analysis = self._parse_json_response(raw_response)

        if not analysis:
            analysis = self._build_fallback_pestel(subject, industry)

        analysis["metadata"] = {
            "subject": subject,
            "industry": industry,
            "data_enriched": enrich_with_data,
            "domain_profile_used": domain_profile is not None,
            "generated_at": datetime.utcnow().isoformat(),
            "model": "llm" if self.llm else "demo",
        }

        return {
            "analysis": analysis,
            "type": "pestel",
            "insights": self._extract_insights(analysis, "pestel"),
        }

    async def generate_combined(
        self,
        subject: str,
        industry: str = "",
        context: Optional[dict] = None,
        domain_profile: Optional[dict] = None,
    ) -> dict:
        """
        Generate both SWOT and PESTEL analyses and cross-reference them.

        Returns:
            Dict with both analyses and a combined strategic summary.
        """
        swot_result = await self.generate_swot(
            subject, industry, context, domain_profile
        )
        pestel_result = await self.generate_pestel(
            subject, industry, context, domain_profile, enrich_with_data=False
        )

        return {
            "swot": swot_result,
            "pestel": pestel_result,
            "combined_insights": {
                "total_factors_identified": (
                    self._count_factors(swot_result.get("analysis", {}), "swot")
                    + self._count_factors(pestel_result.get("analysis", {}), "pestel")
                ),
                "high_impact_factors": self._get_high_impact_factors(
                    swot_result.get("analysis", {}),
                    pestel_result.get("analysis", {}),
                ),
                "generated_at": datetime.utcnow().isoformat(),
            },
        }

    # ------------------------------------------------------------------
    # Data enrichment
    # ------------------------------------------------------------------

    async def _gather_data_context(self, subject: str, industry: str) -> str:
        """Gather real data from available sources to enrich the analysis."""
        context_parts = []

        # News data
        if self.news_client and self.news_client.is_configured:
            try:
                news = await self.news_client.search_news(
                    query=f"{subject} {industry}",
                    days_back=14,
                    page_size=5,
                )
                if news:
                    headlines = [a["title"] for a in news[:5] if a.get("title")]
                    context_parts.append(
                        f"Recent news headlines:\n" + "\n".join(f"- {h}" for h in headlines)
                    )
            except Exception as exc:
                logger.debug("News enrichment failed: %s", exc)

        # Wikipedia data
        if self.wikipedia_client:
            try:
                wiki_info = await self.wikipedia_client.get_summary(
                    subject.replace(" ", "_")
                )
                if wiki_info.get("extract"):
                    context_parts.append(
                        f"Background information:\n{wiki_info['extract'][:500]}"
                    )
            except Exception as exc:
                logger.debug("Wikipedia enrichment failed: %s", exc)

        # Trends data
        if self.trends_client:
            try:
                trends = await self.trends_client.get_related_queries(subject)
                top_queries = trends.get("top", [])[:5]
                if top_queries:
                    queries_text = ", ".join(
                        q.get("query", "") for q in top_queries if q.get("query")
                    )
                    context_parts.append(f"Related search trends: {queries_text}")
            except Exception as exc:
                logger.debug("Trends enrichment failed: %s", exc)

        if context_parts:
            return "Real-world data for context:\n\n" + "\n\n".join(context_parts)
        return ""

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _call_llm(self, prompt: str) -> str:
        """Call the LLM and return the response text."""
        if self.llm:
            try:
                messages = [
                    {
                        "role": "system",
                        "content": (
                            "You are a senior business strategy consultant. "
                            "Always return valid JSON. No markdown code fences."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ]
                return await self.llm.generate(messages)
            except Exception as exc:
                logger.error("LLM call failed: %s", exc)
                return ""
        return ""

    @staticmethod
    def _parse_json_response(text: str) -> Optional[dict]:
        """Attempt to parse a JSON response, handling common LLM quirks."""
        if not text:
            return None
        # Strip markdown code fences if present
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1]
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to find JSON object in the text
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    return json.loads(text[start:end])
                except json.JSONDecodeError:
                    pass
            logger.warning("Failed to parse JSON from LLM response")
            return None

    @staticmethod
    def _build_fallback_swot(subject: str, industry: str) -> dict:
        """Build a placeholder SWOT structure when LLM is unavailable."""
        return {
            "subject": subject,
            "industry": industry,
            "summary": (
                f"[Demo Mode] SWOT analysis for {subject} in {industry or 'general'} industry. "
                "Configure an LLM to generate full analysis."
            ),
            "strengths": [{"factor": "Analysis requires LLM configuration", "impact": "high", "confidence": "low", "evidence": "N/A", "recommendations": ["Configure OPENAI_API_KEY"]}],
            "weaknesses": [{"factor": "Analysis requires LLM configuration", "impact": "high", "confidence": "low", "evidence": "N/A", "recommendations": ["Configure OPENAI_API_KEY"]}],
            "opportunities": [{"factor": "Analysis requires LLM configuration", "impact": "high", "confidence": "low", "evidence": "N/A", "recommendations": ["Configure OPENAI_API_KEY"]}],
            "threats": [{"factor": "Analysis requires LLM configuration", "impact": "high", "confidence": "low", "evidence": "N/A", "recommendations": ["Configure OPENAI_API_KEY"]}],
            "cross_analysis": {"so_strategies": [], "wo_strategies": [], "st_strategies": [], "wt_strategies": []},
            "priority_actions": ["Configure LLM API key for full analysis"],
        }

    @staticmethod
    def _build_fallback_pestel(subject: str, industry: str) -> dict:
        """Build a placeholder PESTEL structure when LLM is unavailable."""
        placeholder = [{"factor": "Analysis requires LLM configuration", "impact": "medium", "likelihood": "medium", "timeframe": "medium-term", "evidence": "N/A", "implications": ["Configure OPENAI_API_KEY"]}]
        return {
            "subject": subject,
            "industry": industry,
            "summary": f"[Demo Mode] PESTEL analysis for {subject}. Configure an LLM to generate full analysis.",
            "political": placeholder,
            "economic": placeholder,
            "social": placeholder,
            "technological": placeholder,
            "environmental": placeholder,
            "legal": placeholder,
            "risk_matrix": {"high_impact_high_likelihood": [], "high_impact_low_likelihood": [], "low_impact_high_likelihood": [], "low_impact_low_likelihood": []},
            "strategic_recommendations": ["Configure LLM API key for full analysis"],
        }

    @staticmethod
    def _extract_insights(analysis: dict, analysis_type: str) -> list[dict]:
        """Extract key insights from an analysis for storage/display."""
        insights = []
        if analysis_type == "swot":
            for category in ["strengths", "weaknesses", "opportunities", "threats"]:
                items = analysis.get(category, [])
                high_impact = [i for i in items if isinstance(i, dict) and i.get("impact") == "high"]
                if high_impact:
                    insights.append({
                        "category": category,
                        "high_impact_count": len(high_impact),
                        "factors": [i.get("factor", "") for i in high_impact],
                    })
        elif analysis_type == "pestel":
            for category in ["political", "economic", "social", "technological", "environmental", "legal"]:
                items = analysis.get(category, [])
                high_impact = [i for i in items if isinstance(i, dict) and i.get("impact") == "high"]
                if high_impact:
                    insights.append({
                        "category": category,
                        "high_impact_count": len(high_impact),
                        "factors": [i.get("factor", "") for i in high_impact],
                    })
        return insights

    @staticmethod
    def _count_factors(analysis: dict, analysis_type: str) -> int:
        """Count total factors in an analysis."""
        categories = (
            ["strengths", "weaknesses", "opportunities", "threats"]
            if analysis_type == "swot"
            else ["political", "economic", "social", "technological", "environmental", "legal"]
        )
        return sum(len(analysis.get(c, [])) for c in categories)

    @staticmethod
    def _get_high_impact_factors(swot: dict, pestel: dict) -> list[str]:
        """Extract all high-impact factors from both analyses."""
        factors = []
        for category in ["strengths", "weaknesses", "opportunities", "threats"]:
            for item in swot.get(category, []):
                if isinstance(item, dict) and item.get("impact") == "high":
                    factors.append(f"[SWOT/{category}] {item.get('factor', '')}")
        for category in ["political", "economic", "social", "technological", "environmental", "legal"]:
            for item in pestel.get(category, []):
                if isinstance(item, dict) and item.get("impact") == "high":
                    factors.append(f"[PESTEL/{category}] {item.get('factor', '')}")
        return factors
