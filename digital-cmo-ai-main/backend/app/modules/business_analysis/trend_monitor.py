"""
Trend Monitoring Engine

Monitors industry trends, search patterns, news cycles, and market
signals. Aggregates data from Google Trends, NewsAPI, and web sources
to provide real-time trend intelligence and alerts.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


TREND_ANALYSIS_TEMPLATE = """You are a senior market intelligence analyst. Analyse the following trend data and provide strategic insights.

**Industry:** {industry}
**Monitoring Period:** {period}
**Keywords Tracked:** {keywords}

{trend_data}

Provide a comprehensive trend analysis. Return as a JSON object with this EXACT structure:
{{
    "industry": "{industry}",
    "analysis_period": "{period}",
    "generated_at": "<ISO timestamp>",
    "executive_summary": "<3-4 sentence overview of key trends>",
    "trending_topics": [
        {{
            "topic": "<trend topic>",
            "direction": "rising|stable|declining",
            "momentum": "accelerating|steady|decelerating",
            "relevance": "high|medium|low",
            "description": "<brief description>",
            "business_impact": "<how this affects the business>"
        }}
    ],
    "emerging_signals": [
        {{
            "signal": "<emerging trend or weak signal>",
            "confidence": "high|medium|low",
            "potential_impact": "high|medium|low",
            "timeframe": "<when this might become significant>",
            "recommended_action": "<what to do about it>"
        }}
    ],
    "news_themes": [
        {{
            "theme": "<recurring news theme>",
            "frequency": "high|medium|low",
            "sentiment": "positive|neutral|negative",
            "key_stories": ["<headline 1>", "<headline 2>"]
        }}
    ],
    "competitive_signals": [
        {{
            "signal": "<competitive movement or announcement>",
            "competitor": "<company name if applicable>",
            "significance": "high|medium|low",
            "response_needed": true/false
        }}
    ],
    "recommendations": [
        {{
            "recommendation": "<actionable recommendation>",
            "priority": "high|medium|low",
            "category": "product|marketing|strategy|operations",
            "rationale": "<why this matters now>"
        }}
    ],
    "risk_alerts": [
        {{
            "risk": "<identified risk>",
            "severity": "critical|high|medium|low",
            "probability": "high|medium|low",
            "mitigation": "<suggested mitigation>"
        }}
    ]
}}

Be specific, data-driven, and actionable. Return ONLY valid JSON.
"""


class TrendMonitor:
    """
    Monitors and analyses industry trends using multiple data sources.

    Aggregates signals from Google Trends, news APIs, and web sources
    to provide actionable trend intelligence.
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

    async def monitor_trends(
        self,
        keywords: list[str],
        industry: str = "",
        timeframe: str = "today 3-m",
        domain_profile: Optional[dict] = None,
    ) -> dict:
        """
        Perform comprehensive trend monitoring for given keywords.

        Args:
            keywords: Keywords to monitor.
            industry: Industry context.
            timeframe: Google Trends timeframe string.
            domain_profile: Optional domain profile for industry context.

        Returns:
            Structured trend monitoring report.
        """
        if domain_profile:
            extra_keywords = domain_profile.get("trend_keywords", [])
            keywords = list(set(keywords + extra_keywords))

        # Gather trend data from all sources
        trend_data = await self._gather_trend_data(keywords, industry, timeframe)

        # Generate analysis via LLM
        period = self._timeframe_to_readable(timeframe)
        prompt = TREND_ANALYSIS_TEMPLATE.format(
            industry=industry or "General",
            period=period,
            keywords=", ".join(keywords),
            trend_data=trend_data,
        )

        raw_response = await self._call_llm(prompt)
        analysis = self._parse_json_response(raw_response)

        if not analysis:
            analysis = self._build_fallback_analysis(keywords, industry)

        analysis["metadata"] = {
            "keywords_monitored": keywords,
            "industry": industry,
            "timeframe": timeframe,
            "sources_used": self._get_available_sources(),
            "generated_at": datetime.utcnow().isoformat(),
        }

        return {
            "analysis": analysis,
            "type": "trend_monitoring",
            "raw_data": {
                "trend_data_summary": trend_data[:2000] if trend_data else "",
            },
            "insights": self._extract_insights(analysis),
        }

    async def get_trending_now(
        self,
        industry: str = "",
        country: str = "united_states",
        domain_profile: Optional[dict] = None,
    ) -> dict:
        """
        Get currently trending topics relevant to an industry.

        Args:
            industry: Industry to focus on.
            country: Country for trending searches.
            domain_profile: Optional domain profile.

        Returns:
            Dict with trending topics and relevance scores.
        """
        result = {
            "industry": industry,
            "country": country,
            "generated_at": datetime.utcnow().isoformat(),
            "trending_searches": [],
            "industry_news": [],
            "search_interest": {},
        }

        # Get trending searches
        if self.trends_client:
            try:
                trending = await self.trends_client.get_trending_searches(country)
                result["trending_searches"] = trending[:20]
            except Exception as exc:
                logger.debug("Trending searches failed: %s", exc)

        # Get industry news
        if self.news_client and self.news_client.is_configured:
            try:
                category = self._industry_to_news_category(industry)
                headlines = await self.news_client.get_top_headlines(
                    category=category, page_size=10
                )
                result["industry_news"] = headlines
            except Exception as exc:
                logger.debug("Industry news failed: %s", exc)

        # Get search interest for domain keywords
        if self.trends_client and domain_profile:
            keywords = domain_profile.get("trend_keywords", [])[:5]
            if keywords:
                try:
                    interest = await self.trends_client.get_interest_over_time(
                        keywords, timeframe="now 7-d"
                    )
                    result["search_interest"] = interest
                except Exception as exc:
                    logger.debug("Search interest failed: %s", exc)

        return result

    async def compare_trend_keywords(
        self,
        keywords: list[str],
        timeframe: str = "today 12-m",
        geo: str = "",
    ) -> dict:
        """
        Compare search interest across multiple keywords.

        Args:
            keywords: Keywords to compare (max 5).
            timeframe: Time period for comparison.
            geo: Geographic filter.

        Returns:
            Comparison data with rankings and trends.
        """
        keywords = keywords[:5]
        result = {
            "keywords": keywords,
            "timeframe": timeframe,
            "geo": geo,
            "generated_at": datetime.utcnow().isoformat(),
        }

        if self.trends_client:
            try:
                interest = await self.trends_client.get_interest_over_time(
                    keywords, timeframe=timeframe, geo=geo
                )
                result["interest_over_time"] = interest

                # Calculate averages and rankings
                data_points = interest.get("data", [])
                if data_points:
                    averages = {}
                    for kw in keywords:
                        values = [
                            d.get(kw, 0) for d in data_points
                            if isinstance(d.get(kw), (int, float))
                        ]
                        if values:
                            averages[kw] = {
                                "average": round(sum(values) / len(values), 1),
                                "peak": max(values),
                                "latest": values[-1] if values else 0,
                                "trend": self._calculate_trend(values),
                            }
                    result["keyword_stats"] = averages

                    # Rank by average interest
                    ranked = sorted(
                        averages.items(),
                        key=lambda x: x[1]["average"],
                        reverse=True,
                    )
                    result["ranking"] = [
                        {"keyword": kw, "rank": i + 1, **stats}
                        for i, (kw, stats) in enumerate(ranked)
                    ]

                # Get regional data
                regional = await self.trends_client.get_interest_by_region(
                    keywords, timeframe=timeframe
                )
                result["regional_interest"] = regional

            except Exception as exc:
                logger.error("Keyword comparison failed: %s", exc)
                result["error"] = str(exc)
        else:
            result["error"] = "Google Trends client not configured"

        return result

    async def detect_anomalies(
        self,
        keywords: list[str],
        timeframe: str = "today 3-m",
        threshold: float = 2.0,
    ) -> dict:
        """
        Detect unusual spikes or drops in search interest.

        Args:
            keywords: Keywords to monitor.
            timeframe: Time period to analyse.
            threshold: Standard deviation threshold for anomaly detection.

        Returns:
            Dict with detected anomalies and their details.
        """
        anomalies = []

        if not self.trends_client:
            return {"anomalies": [], "error": "Trends client not configured"}

        try:
            interest = await self.trends_client.get_interest_over_time(
                keywords[:5], timeframe=timeframe
            )
            data_points = interest.get("data", [])

            if not data_points:
                return {"anomalies": [], "keywords": keywords}

            import numpy as np

            for kw in keywords[:5]:
                values = [
                    d.get(kw, 0) for d in data_points
                    if isinstance(d.get(kw), (int, float))
                ]
                if len(values) < 5:
                    continue

                arr = np.array(values, dtype=float)
                mean = arr.mean()
                std = arr.std()

                if std == 0:
                    continue

                for i, val in enumerate(values):
                    z_score = (val - mean) / std
                    if abs(z_score) >= threshold:
                        anomalies.append({
                            "keyword": kw,
                            "date": data_points[i].get("date", ""),
                            "value": val,
                            "z_score": round(z_score, 2),
                            "type": "spike" if z_score > 0 else "drop",
                            "severity": (
                                "critical" if abs(z_score) >= 3
                                else "high" if abs(z_score) >= 2.5
                                else "medium"
                            ),
                        })

        except Exception as exc:
            logger.error("Anomaly detection failed: %s", exc)
            return {"anomalies": [], "error": str(exc)}

        return {
            "anomalies": sorted(anomalies, key=lambda x: abs(x["z_score"]), reverse=True),
            "keywords": keywords,
            "timeframe": timeframe,
            "threshold": threshold,
            "total_anomalies": len(anomalies),
            "generated_at": datetime.utcnow().isoformat(),
        }

    async def generate_trend_report(
        self,
        industry: str,
        domain_profile: Optional[dict] = None,
        include_competitors: bool = True,
    ) -> dict:
        """
        Generate a comprehensive trend report for an industry.

        Args:
            industry: Industry to report on.
            domain_profile: Optional domain profile.
            include_competitors: Whether to include competitor trend data.

        Returns:
            Comprehensive trend report dict.
        """
        keywords = [industry]
        competitors = []

        if domain_profile:
            keywords.extend(domain_profile.get("trend_keywords", []))
            if include_competitors:
                competitors = domain_profile.get("typical_competitors", [])[:5]

        # Core trend monitoring
        trend_result = await self.monitor_trends(
            keywords=keywords[:10],
            industry=industry,
            timeframe="today 3-m",
            domain_profile=domain_profile,
        )

        # Keyword comparison
        comparison = await self.compare_trend_keywords(
            keywords=keywords[:5],
            timeframe="today 12-m",
        )

        # Anomaly detection
        anomalies = await self.detect_anomalies(
            keywords=keywords[:5],
            timeframe="today 3-m",
        )

        # Competitor trends
        competitor_trends = {}
        if competitors and self.trends_client:
            try:
                comp_interest = await self.trends_client.get_interest_over_time(
                    competitors[:5], timeframe="today 12-m"
                )
                competitor_trends = comp_interest
            except Exception:
                pass

        report = {
            "report_type": "comprehensive_trend_report",
            "industry": industry,
            "generated_at": datetime.utcnow().isoformat(),
            "trend_analysis": trend_result.get("analysis", {}),
            "keyword_comparison": comparison,
            "anomalies": anomalies,
            "competitor_trends": competitor_trends,
            "domain_profile_used": domain_profile.get("name") if domain_profile else None,
        }

        return report

    # ------------------------------------------------------------------
    # Data gathering
    # ------------------------------------------------------------------

    async def _gather_trend_data(
        self,
        keywords: list[str],
        industry: str,
        timeframe: str,
    ) -> str:
        """Gather trend data from all available sources."""
        parts = []

        # Google Trends data
        if self.trends_client:
            try:
                interest = await self.trends_client.get_interest_over_time(
                    keywords[:5], timeframe=timeframe
                )
                data = interest.get("data", [])
                if data:
                    # Summarise: first, last, peak
                    summary_lines = ["Search interest trends:"]
                    for kw in keywords[:5]:
                        values = [
                            d.get(kw, 0) for d in data
                            if isinstance(d.get(kw), (int, float))
                        ]
                        if values:
                            summary_lines.append(
                                f"  {kw}: start={values[0]}, end={values[-1]}, "
                                f"peak={max(values)}, avg={sum(values)//len(values)}"
                            )
                    parts.append("\n".join(summary_lines))

                # Related queries
                for kw in keywords[:3]:
                    related = await self.trends_client.get_related_queries(kw, timeframe=timeframe)
                    top = related.get("top", [])[:5]
                    rising = related.get("rising", [])[:5]
                    if top or rising:
                        lines = [f"Related queries for '{kw}':"]
                        if top:
                            lines.append(
                                f"  Top: {', '.join(q.get('query', '') for q in top)}"
                            )
                        if rising:
                            lines.append(
                                f"  Rising: {', '.join(q.get('query', '') for q in rising)}"
                            )
                        parts.append("\n".join(lines))

            except Exception as exc:
                logger.debug("Trends data gathering failed: %s", exc)

        # News data
        if self.news_client and self.news_client.is_configured:
            try:
                query = f"{industry} {' '.join(keywords[:3])}"
                news = await self.news_client.search_news(
                    query=query, days_back=14, page_size=10
                )
                if news:
                    parts.append("Recent news headlines:")
                    for article in news[:10]:
                        title = article.get("title", "")
                        source = article.get("source_name", "")
                        date = article.get("published_at", "")[:10]
                        if title:
                            parts.append(f"  [{date}] {title} ({source})")
            except Exception as exc:
                logger.debug("News data gathering failed: %s", exc)

        return "\n\n".join(parts) if parts else "No external data available."

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
                            "You are a senior market intelligence analyst. "
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
    def _timeframe_to_readable(timeframe: str) -> str:
        mapping = {
            "now 1-H": "Last hour",
            "now 4-H": "Last 4 hours",
            "now 1-d": "Last day",
            "now 7-d": "Last 7 days",
            "today 1-m": "Last month",
            "today 3-m": "Last 3 months",
            "today 12-m": "Last 12 months",
            "today 5-y": "Last 5 years",
        }
        return mapping.get(timeframe, timeframe)

    @staticmethod
    def _industry_to_news_category(industry: str) -> str:
        mapping = {
            "tech": "technology",
            "saas": "technology",
            "healthcare": "health",
            "health": "health",
            "finance": "business",
            "fintech": "business",
            "education": "general",
            "travel": "general",
            "real estate": "business",
            "ecommerce": "business",
            "retail": "business",
        }
        industry_lower = industry.lower()
        for key, category in mapping.items():
            if key in industry_lower:
                return category
        return "business"

    @staticmethod
    def _calculate_trend(values: list) -> str:
        if len(values) < 2:
            return "insufficient_data"
        first_half = values[: len(values) // 2]
        second_half = values[len(values) // 2 :]
        avg_first = sum(first_half) / len(first_half) if first_half else 0
        avg_second = sum(second_half) / len(second_half) if second_half else 0
        if avg_second > avg_first * 1.1:
            return "rising"
        elif avg_second < avg_first * 0.9:
            return "declining"
        return "stable"

    def _get_available_sources(self) -> list[str]:
        sources = []
        if self.trends_client:
            sources.append("google_trends")
        if self.news_client and self.news_client.is_configured:
            sources.append("news_api")
        if self.wikipedia_client:
            sources.append("wikipedia")
        if self.web_scraper:
            sources.append("web_scraper")
        return sources

    @staticmethod
    def _build_fallback_analysis(keywords: list[str], industry: str) -> dict:
        return {
            "industry": industry,
            "executive_summary": (
                f"[Demo Mode] Trend analysis for {industry or 'general'} industry. "
                "Configure data sources and LLM for full analysis."
            ),
            "trending_topics": [],
            "emerging_signals": [],
            "news_themes": [],
            "competitive_signals": [],
            "recommendations": [],
            "risk_alerts": [],
        }

    @staticmethod
    def _extract_insights(analysis: dict) -> list[dict]:
        insights = []
        trending = analysis.get("trending_topics", [])
        rising = [t for t in trending if isinstance(t, dict) and t.get("direction") == "rising"]
        if rising:
            insights.append({
                "type": "rising_trends",
                "count": len(rising),
                "topics": [t.get("topic", "") for t in rising[:5]],
            })
        risks = analysis.get("risk_alerts", [])
        critical = [r for r in risks if isinstance(r, dict) and r.get("severity") in ("critical", "high")]
        if critical:
            insights.append({
                "type": "risk_alerts",
                "count": len(critical),
                "risks": [r.get("risk", "") for r in critical[:3]],
            })
        signals = analysis.get("emerging_signals", [])
        high_impact = [s for s in signals if isinstance(s, dict) and s.get("potential_impact") == "high"]
        if high_impact:
            insights.append({
                "type": "emerging_signals",
                "count": len(high_impact),
                "signals": [s.get("signal", "") for s in high_impact[:3]],
            })
        return insights
