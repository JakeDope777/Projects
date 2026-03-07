"""
Competitor Analysis Engine

Provides automated competitor research, comparison matrix generation,
and competitive intelligence gathering using web scraping, Wikipedia,
news sources, and LLM-powered analysis.
"""

import json
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


COMPETITOR_ANALYSIS_TEMPLATE = """You are a senior competitive intelligence analyst. Analyse the following competitors:

**Companies:** {companies}
**Industry:** {industry}
**Context:** {context}

{enrichment_data}

For each competitor, provide a detailed analysis. Return your analysis as a JSON object with this EXACT structure:
{{
    "analysis_date": "<ISO timestamp>",
    "industry": "{industry}",
    "competitors": [
        {{
            "name": "<company name>",
            "overview": "<2-3 sentence company overview>",
            "founded": "<year or 'Unknown'>",
            "headquarters": "<location or 'Unknown'>",
            "estimated_size": "<employee count range or 'Unknown'>",
            "products_services": [
                {{
                    "name": "<product/service name>",
                    "description": "<brief description>",
                    "target_market": "<target audience>"
                }}
            ],
            "market_positioning": {{
                "segment": "<premium|mid-market|budget|enterprise|SMB>",
                "unique_value_proposition": "<their key differentiator>",
                "target_audience": "<primary customer profile>"
            }},
            "strengths": ["<strength 1>", "<strength 2>"],
            "weaknesses": ["<weakness 1>", "<weakness 2>"],
            "marketing_strategy": {{
                "channels": ["<channel 1>", "<channel 2>"],
                "content_approach": "<description>",
                "brand_positioning": "<description>"
            }},
            "pricing_model": {{
                "type": "<subscription|freemium|one-time|usage-based|custom>",
                "price_range": "<if known>",
                "notes": "<additional pricing info>"
            }},
            "technology_stack": ["<known technologies>"],
            "recent_developments": ["<recent news or changes>"],
            "threat_level": "high|medium|low",
            "threat_reasoning": "<why this threat level>"
        }}
    ],
    "comparison_matrix": {{
        "dimensions": ["<dimension 1>", "<dimension 2>", "..."],
        "ratings": {{
            "<company name>": {{
                "<dimension>": {{
                    "score": <1-5>,
                    "notes": "<brief note>"
                }}
            }}
        }}
    }},
    "competitive_landscape": {{
        "market_leaders": ["<company names>"],
        "challengers": ["<company names>"],
        "niche_players": ["<company names>"],
        "emerging_threats": ["<company names>"]
    }},
    "strategic_recommendations": [
        {{
            "recommendation": "<actionable recommendation>",
            "priority": "high|medium|low",
            "rationale": "<why this matters>"
        }}
    ],
    "gaps_and_opportunities": ["<market gap or opportunity>"]
}}

Be specific, data-driven, and actionable. Return ONLY valid JSON.
"""

QUICK_COMPARISON_TEMPLATE = """Compare these companies across key business dimensions:

**Companies:** {companies}
**Dimensions:** {dimensions}

Return a JSON object with:
{{
    "matrix": {{
        "<company>": {{
            "<dimension>": {{
                "score": <1-5>,
                "notes": "<brief explanation>"
            }}
        }}
    }},
    "summary": "<2-3 sentence comparison summary>",
    "winner_by_dimension": {{
        "<dimension>": "<company name>"
    }}
}}

Return ONLY valid JSON.
"""


class CompetitorAnalyzer:
    """
    Automated competitor analysis engine with web research capabilities,
    comparison matrix generation, and competitive intelligence gathering.
    """

    DEFAULT_COMPARISON_DIMENSIONS = [
        "Product Quality",
        "Pricing",
        "Market Share",
        "Brand Recognition",
        "Innovation",
        "Customer Support",
        "Digital Presence",
        "Scalability",
    ]

    def __init__(
        self,
        llm_client=None,
        news_client=None,
        wikipedia_client=None,
        web_scraper=None,
        trends_client=None,
    ):
        self.llm = llm_client
        self.news_client = news_client
        self.wikipedia_client = wikipedia_client
        self.web_scraper = web_scraper
        self.trends_client = trends_client

    async def analyze_competitors(
        self,
        company_names: list[str],
        industry: str = "",
        context: Optional[dict] = None,
        domain_profile: Optional[dict] = None,
        enrich_with_data: bool = True,
    ) -> dict:
        """
        Perform a comprehensive competitor analysis with automated research.

        Args:
            company_names: List of competitor company names.
            industry: Industry context.
            context: Additional context.
            domain_profile: Domain profile with typical competitors.
            enrich_with_data: Whether to fetch real data.

        Returns:
            Structured competitor analysis dict.
        """
        context = context or {}
        enrichment_data = ""

        if enrich_with_data:
            enrichment_data = await self._gather_competitor_data(
                company_names, industry
            )

        if domain_profile and domain_profile.get("typical_competitors"):
            typical = domain_profile["typical_competitors"]
            enrichment_data += (
                f"\n\nTypical competitors in this industry: {', '.join(typical)}"
            )

        prompt = COMPETITOR_ANALYSIS_TEMPLATE.format(
            companies=", ".join(company_names),
            industry=industry or "General",
            context=json.dumps(context, default=str),
            enrichment_data=enrichment_data,
        )

        raw_response = await self._call_llm(prompt)
        analysis = self._parse_json_response(raw_response)

        if not analysis:
            analysis = self._build_fallback_analysis(company_names, industry)

        analysis["metadata"] = {
            "companies_analyzed": company_names,
            "industry": industry,
            "data_enriched": enrich_with_data,
            "generated_at": datetime.utcnow().isoformat(),
        }

        return {
            "analysis": analysis,
            "type": "competitor_analysis",
            "insights": self._extract_insights(analysis),
        }

    async def quick_comparison(
        self,
        company_names: list[str],
        dimensions: Optional[list[str]] = None,
    ) -> dict:
        """
        Generate a quick comparison matrix for the given companies.

        Args:
            company_names: Companies to compare.
            dimensions: Comparison dimensions (uses defaults if not provided).

        Returns:
            Comparison matrix dict.
        """
        dimensions = dimensions or self.DEFAULT_COMPARISON_DIMENSIONS

        prompt = QUICK_COMPARISON_TEMPLATE.format(
            companies=", ".join(company_names),
            dimensions=", ".join(dimensions),
        )

        raw_response = await self._call_llm(prompt)
        result = self._parse_json_response(raw_response)

        if not result:
            result = {
                "matrix": {
                    name: {d: {"score": 0, "notes": "LLM required"} for d in dimensions}
                    for name in company_names
                },
                "summary": "[Demo Mode] Configure LLM for comparison.",
                "winner_by_dimension": {},
            }

        result["metadata"] = {
            "companies": company_names,
            "dimensions": dimensions,
            "generated_at": datetime.utcnow().isoformat(),
        }

        return result

    async def research_company(
        self,
        company_name: str,
        website_url: Optional[str] = None,
    ) -> dict:
        """
        Research a single company using all available data sources.

        Args:
            company_name: Name of the company.
            website_url: Optional company website URL.

        Returns:
            Comprehensive company research dict.
        """
        research = {
            "company": company_name,
            "sources_used": [],
            "generated_at": datetime.utcnow().isoformat(),
        }

        # Wikipedia research
        if self.wikipedia_client:
            try:
                wiki_data = await self.wikipedia_client.get_company_info(company_name)
                if wiki_data.get("found"):
                    research["wikipedia"] = wiki_data
                    research["sources_used"].append("wikipedia")
            except Exception as exc:
                logger.debug("Wikipedia research failed for %s: %s", company_name, exc)

        # News research
        if self.news_client and self.news_client.is_configured:
            try:
                news = await self.news_client.search_news(
                    query=company_name, days_back=30, page_size=5
                )
                if news:
                    research["recent_news"] = news
                    research["sources_used"].append("news_api")
            except Exception as exc:
                logger.debug("News research failed for %s: %s", company_name, exc)

        # Website scraping
        if self.web_scraper and website_url:
            try:
                site_data = await self.web_scraper.extract_company_data(website_url)
                if not site_data.get("error"):
                    research["website_data"] = site_data
                    research["sources_used"].append("web_scraper")
            except Exception as exc:
                logger.debug("Web scraping failed for %s: %s", company_name, exc)

        # Search trends
        if self.trends_client:
            try:
                trends = await self.trends_client.get_interest_over_time(
                    [company_name], timeframe="today 12-m"
                )
                if trends.get("data"):
                    research["search_trends"] = trends
                    research["sources_used"].append("google_trends")
            except Exception as exc:
                logger.debug("Trends research failed for %s: %s", company_name, exc)

        return research

    async def track_competitors(
        self,
        company_names: list[str],
        metrics: Optional[list[str]] = None,
    ) -> dict:
        """
        Set up competitor tracking with periodic data collection.

        Args:
            company_names: Companies to track.
            metrics: Specific metrics to monitor.

        Returns:
            Tracking configuration and initial data snapshot.
        """
        metrics = metrics or [
            "news_mentions",
            "search_interest",
            "website_changes",
        ]

        tracking_data = {
            "tracked_companies": company_names,
            "metrics": metrics,
            "snapshot_date": datetime.utcnow().isoformat(),
            "snapshots": {},
        }

        for company in company_names:
            snapshot = {"company": company}

            if "news_mentions" in metrics and self.news_client and self.news_client.is_configured:
                try:
                    news = await self.news_client.search_news(
                        company, days_back=7, page_size=5
                    )
                    snapshot["news_mentions"] = {
                        "count": len(news),
                        "recent_headlines": [a["title"] for a in news[:3]],
                    }
                except Exception:
                    snapshot["news_mentions"] = {"count": 0, "recent_headlines": []}

            if "search_interest" in metrics and self.trends_client:
                try:
                    trends = await self.trends_client.get_interest_over_time(
                        [company], timeframe="now 7-d"
                    )
                    data_points = trends.get("data", [])
                    if data_points:
                        values = [
                            d.get(company, 0) for d in data_points
                            if isinstance(d.get(company), (int, float))
                        ]
                        snapshot["search_interest"] = {
                            "average": sum(values) / len(values) if values else 0,
                            "trend": "up" if len(values) > 1 and values[-1] > values[0] else "down",
                            "data_points": len(values),
                        }
                    else:
                        snapshot["search_interest"] = {"average": 0, "trend": "unknown", "data_points": 0}
                except Exception:
                    snapshot["search_interest"] = {"average": 0, "trend": "unknown", "data_points": 0}

            tracking_data["snapshots"][company] = snapshot

        return tracking_data

    # ------------------------------------------------------------------
    # Data gathering
    # ------------------------------------------------------------------

    async def _gather_competitor_data(
        self, company_names: list[str], industry: str
    ) -> str:
        """Gather real data about competitors from available sources."""
        parts = []

        for company in company_names[:5]:
            company_parts = [f"\n--- Data for {company} ---"]

            if self.wikipedia_client:
                try:
                    wiki = await self.wikipedia_client.get_company_info(company)
                    if wiki.get("found") and wiki.get("summary"):
                        company_parts.append(
                            f"Wikipedia: {wiki['summary'][:300]}"
                        )
                except Exception:
                    pass

            if self.news_client and self.news_client.is_configured:
                try:
                    news = await self.news_client.search_news(
                        company, days_back=14, page_size=3
                    )
                    if news:
                        headlines = [a["title"] for a in news if a.get("title")]
                        company_parts.append(
                            f"Recent news: {'; '.join(headlines[:3])}"
                        )
                except Exception:
                    pass

            if len(company_parts) > 1:
                parts.append("\n".join(company_parts))

        return "\n".join(parts) if parts else ""

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _call_llm(self, prompt: str) -> str:
        if self.llm:
            try:
                messages = [
                    {
                        "role": "system",
                        "content": (
                            "You are a senior competitive intelligence analyst. "
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
        if not text:
            return None
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1]
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    return json.loads(text[start:end])
                except json.JSONDecodeError:
                    pass
            return None

    @staticmethod
    def _build_fallback_analysis(company_names: list[str], industry: str) -> dict:
        competitors = []
        for name in company_names:
            competitors.append({
                "name": name,
                "overview": f"[Demo Mode] Analysis for {name} requires LLM configuration.",
                "founded": "Unknown",
                "headquarters": "Unknown",
                "estimated_size": "Unknown",
                "products_services": [],
                "market_positioning": {"segment": "Unknown", "unique_value_proposition": "", "target_audience": ""},
                "strengths": [],
                "weaknesses": [],
                "marketing_strategy": {"channels": [], "content_approach": "", "brand_positioning": ""},
                "pricing_model": {"type": "Unknown", "price_range": "", "notes": ""},
                "technology_stack": [],
                "recent_developments": [],
                "threat_level": "medium",
                "threat_reasoning": "Requires LLM for assessment",
            })
        return {
            "analysis_date": datetime.utcnow().isoformat(),
            "industry": industry,
            "competitors": competitors,
            "comparison_matrix": {"dimensions": [], "ratings": {}},
            "competitive_landscape": {"market_leaders": [], "challengers": [], "niche_players": [], "emerging_threats": []},
            "strategic_recommendations": [],
            "gaps_and_opportunities": [],
        }

    @staticmethod
    def _extract_insights(analysis: dict) -> list[dict]:
        insights = []
        competitors = analysis.get("competitors", [])
        high_threats = [
            c["name"] for c in competitors
            if isinstance(c, dict) and c.get("threat_level") == "high"
        ]
        if high_threats:
            insights.append({
                "type": "high_threat_competitors",
                "companies": high_threats,
                "count": len(high_threats),
            })
        recommendations = analysis.get("strategic_recommendations", [])
        high_priority = [
            r for r in recommendations
            if isinstance(r, dict) and r.get("priority") == "high"
        ]
        if high_priority:
            insights.append({
                "type": "high_priority_recommendations",
                "count": len(high_priority),
                "recommendations": [r.get("recommendation", "") for r in high_priority],
            })
        gaps = analysis.get("gaps_and_opportunities", [])
        if gaps:
            insights.append({
                "type": "market_gaps",
                "count": len(gaps),
                "gaps": gaps[:5],
            })
        return insights
