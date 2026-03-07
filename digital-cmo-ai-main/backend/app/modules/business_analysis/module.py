"""
Business Analysis Module — Enhanced

Orchestrates all business analysis capabilities including market research,
SWOT/PESTEL analysis, competitor analysis, buyer persona generation,
trend monitoring, and industry domain profiles. Integrates with real
data sources (NewsAPI, Google Trends, Wikipedia, web scraping) for
evidence-backed strategic insights.
"""

import logging
from typing import Optional, Any

from .swot_pestel import SWOTPESTELAnalyzer
from .competitor_analysis import CompetitorAnalyzer
from .persona_generator import PersonaGenerator
from .trend_monitor import TrendMonitor
from .domains import DomainProfileManager
from .data_sources import (
    NewsAPIClient,
    GoogleTrendsClient,
    WikipediaClient,
    WebScraper,
)

logger = logging.getLogger(__name__)


class BusinessAnalysisModule:
    """
    Provides strategic research capabilities including market research,
    competitor analysis, SWOT/PESTEL analyses, persona generation,
    trend monitoring, and industry domain profiles.

    Integrates with real data sources for evidence-backed analysis and
    supports pre-configured industry domain profiles for specialised
    research.
    """

    def __init__(
        self,
        llm_client=None,
        memory_manager=None,
        search_client=None,
        news_api_key: Optional[str] = None,
    ):
        self.llm = llm_client
        self.memory = memory_manager
        self.search_client = search_client

        # Initialise data source clients
        self.news_client = NewsAPIClient(api_key=news_api_key)
        self.trends_client = GoogleTrendsClient()
        self.wikipedia_client = WikipediaClient()
        self.web_scraper = WebScraper()

        # Initialise analysis engines
        self.swot_pestel = SWOTPESTELAnalyzer(
            llm_client=llm_client,
            news_client=self.news_client,
            trends_client=self.trends_client,
            wikipedia_client=self.wikipedia_client,
            web_scraper=self.web_scraper,
        )
        self.competitor_analyzer = CompetitorAnalyzer(
            llm_client=llm_client,
            news_client=self.news_client,
            wikipedia_client=self.wikipedia_client,
            web_scraper=self.web_scraper,
            trends_client=self.trends_client,
        )
        self.persona_generator = PersonaGenerator(
            llm_client=llm_client,
            trends_client=self.trends_client,
            news_client=self.news_client,
        )
        self.trend_monitor = TrendMonitor(
            llm_client=llm_client,
            news_client=self.news_client,
            trends_client=self.trends_client,
            wikipedia_client=self.wikipedia_client,
            web_scraper=self.web_scraper,
        )

        # Domain profile manager
        self.domain_manager = DomainProfileManager()

    # ------------------------------------------------------------------
    # Brain orchestrator interface
    # ------------------------------------------------------------------

    async def handle(self, message: str, context: dict) -> dict:
        """
        Generic handler called by the Brain orchestrator.
        Routes to the appropriate analysis function based on message content.
        """
        message_lower = message.lower()
        domain_profile = self._detect_domain(message_lower, context)

        if "swot" in message_lower:
            result = await self.generate_swot(
                subject=message,
                context=context,
                domain_profile=domain_profile,
            )
            return {"response": self._format_response(result)}

        elif "pestel" in message_lower:
            result = await self.generate_pestel(
                subject=message,
                context=context,
                domain_profile=domain_profile,
            )
            return {"response": self._format_response(result)}

        elif "persona" in message_lower:
            result = await self.create_personas(
                subject=message,
                context=context,
                domain_profile=domain_profile,
            )
            return {"response": self._format_response(result)}

        elif "competitor" in message_lower:
            companies = self._extract_company_names(message, context)
            result = await self.analyze_competitors(
                company_names=companies,
                context=context,
                domain_profile=domain_profile,
            )
            return {"response": self._format_response(result)}

        elif any(kw in message_lower for kw in ["trend", "trending", "monitor"]):
            keywords = self._extract_keywords(message)
            result = await self.monitor_trends(
                keywords=keywords,
                context=context,
                domain_profile=domain_profile,
            )
            return {"response": self._format_response(result)}

        elif "domain" in message_lower or "industry profile" in message_lower:
            return {"response": self._format_domains_response()}

        else:
            result = await self.analyze_market(
                query=message,
                context=context,
                domain_profile=domain_profile,
            )
            return {"response": self._format_response(result)}

    # ------------------------------------------------------------------
    # Public API methods
    # ------------------------------------------------------------------

    async def analyze_market(
        self,
        query: str,
        context: Optional[dict] = None,
        domain_profile: Optional[dict] = None,
    ) -> dict:
        """
        Conduct market research with data enrichment.

        Args:
            query: Natural-language research question.
            context: Optional structured context from memory.
            domain_profile: Optional industry domain profile.

        Returns:
            Dict with insights, sources, and analysis sections.
        """
        context = context or {}

        # Gather data from multiple sources
        data_parts = []

        # News data
        if self.news_client.is_configured:
            try:
                news = await self.news_client.search_news(query, days_back=14, page_size=5)
                if news:
                    data_parts.append({
                        "source": "news",
                        "data": news,
                    })
            except Exception as exc:
                logger.debug("News fetch failed: %s", exc)

        # Wikipedia context
        try:
            wiki = await self.wikipedia_client.search(query, limit=3)
            if wiki:
                summaries = []
                for result in wiki[:2]:
                    summary = await self.wikipedia_client.get_summary(result["title"])
                    if summary.get("extract"):
                        summaries.append(summary)
                if summaries:
                    data_parts.append({
                        "source": "wikipedia",
                        "data": summaries,
                    })
        except Exception as exc:
            logger.debug("Wikipedia fetch failed: %s", exc)

        # Trends data
        try:
            trends = await self.trends_client.get_related_queries(query)
            if trends.get("top") or trends.get("rising"):
                data_parts.append({
                    "source": "google_trends",
                    "data": trends,
                })
        except Exception as exc:
            logger.debug("Trends fetch failed: %s", exc)

        # Build enriched prompt
        enrichment = self._format_data_for_prompt(data_parts)
        prompt = self._build_market_research_prompt(query, context, enrichment, domain_profile)

        response = await self._call_llm(prompt)

        # Store in memory
        if self.memory and response:
            try:
                self.memory.store_embedding(
                    f"Market research: {query} - {response[:200]}",
                    metadata={"type": "market_research", "query": query},
                )
            except Exception:
                pass

        sources = []
        for part in data_parts:
            if part["source"] == "news":
                sources.extend(a.get("url", "") for a in part["data"][:5])
            elif part["source"] == "wikipedia":
                sources.extend(s.get("url", "") for s in part["data"] if s.get("url"))

        return {
            "insights": [{"summary": response}],
            "sources": [s for s in sources if s],
            "analysis": {"market_overview": response},
            "data_sources_used": [p["source"] for p in data_parts],
        }

    async def generate_swot(
        self,
        subject: str,
        industry: str = "",
        context: Optional[dict] = None,
        domain_profile: Optional[dict] = None,
    ) -> dict:
        """Create an enhanced SWOT analysis."""
        return await self.swot_pestel.generate_swot(
            subject=subject,
            industry=industry,
            context=context,
            domain_profile=domain_profile,
        )

    async def generate_pestel(
        self,
        subject: str,
        industry: str = "",
        context: Optional[dict] = None,
        domain_profile: Optional[dict] = None,
    ) -> dict:
        """Create an enhanced PESTEL analysis."""
        return await self.swot_pestel.generate_pestel(
            subject=subject,
            industry=industry,
            context=context,
            domain_profile=domain_profile,
        )

    async def generate_combined_analysis(
        self,
        subject: str,
        industry: str = "",
        context: Optional[dict] = None,
        domain_profile: Optional[dict] = None,
    ) -> dict:
        """Generate both SWOT and PESTEL analyses."""
        return await self.swot_pestel.generate_combined(
            subject=subject,
            industry=industry,
            context=context,
            domain_profile=domain_profile,
        )

    async def analyze_competitors(
        self,
        company_names: list[str],
        industry: str = "",
        context: Optional[dict] = None,
        domain_profile: Optional[dict] = None,
    ) -> dict:
        """Perform comprehensive competitor analysis."""
        return await self.competitor_analyzer.analyze_competitors(
            company_names=company_names,
            industry=industry,
            context=context,
            domain_profile=domain_profile,
        )

    async def quick_comparison(
        self,
        company_names: list[str],
        dimensions: Optional[list[str]] = None,
    ) -> dict:
        """Generate a quick competitor comparison matrix."""
        return await self.competitor_analyzer.quick_comparison(
            company_names=company_names,
            dimensions=dimensions,
        )

    async def research_company(
        self,
        company_name: str,
        website_url: Optional[str] = None,
    ) -> dict:
        """Research a single company using all data sources."""
        return await self.competitor_analyzer.research_company(
            company_name=company_name,
            website_url=website_url,
        )

    async def create_personas(
        self,
        subject: str = "",
        industry: str = "",
        target_market: str = "",
        num_personas: int = 3,
        customer_data: Optional[list[dict]] = None,
        context: Optional[dict] = None,
        domain_profile: Optional[dict] = None,
    ) -> dict:
        """Generate buyer personas with optional data clustering."""
        return await self.persona_generator.generate_personas(
            subject=subject,
            industry=industry,
            target_market=target_market,
            num_personas=num_personas,
            customer_data=customer_data,
            context=context,
            domain_profile=domain_profile,
        )

    async def monitor_trends(
        self,
        keywords: Optional[list[str]] = None,
        industry: str = "",
        timeframe: str = "today 3-m",
        context: Optional[dict] = None,
        domain_profile: Optional[dict] = None,
    ) -> dict:
        """Monitor industry trends."""
        keywords = keywords or [industry] if industry else ["market trends"]
        return await self.trend_monitor.monitor_trends(
            keywords=keywords,
            industry=industry,
            timeframe=timeframe,
            domain_profile=domain_profile,
        )

    async def get_trending_now(
        self,
        industry: str = "",
        domain_profile: Optional[dict] = None,
    ) -> dict:
        """Get currently trending topics."""
        return await self.trend_monitor.get_trending_now(
            industry=industry,
            domain_profile=domain_profile,
        )

    async def generate_trend_report(
        self,
        industry: str,
        domain_profile: Optional[dict] = None,
    ) -> dict:
        """Generate a comprehensive trend report."""
        return await self.trend_monitor.generate_trend_report(
            industry=industry,
            domain_profile=domain_profile,
        )

    # ------------------------------------------------------------------
    # Domain profile methods
    # ------------------------------------------------------------------

    def list_domains(self) -> list[dict]:
        """List all available industry domain profiles."""
        return self.domain_manager.list_domains()

    def get_domain_profile(self, domain_id: str) -> Optional[dict]:
        """Get a specific domain profile."""
        return self.domain_manager.get_profile(domain_id)

    def get_domain_kpis(self, domain_id: str) -> list[dict]:
        """Get KPIs for a specific domain."""
        return self.domain_manager.get_kpis(domain_id)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _detect_domain(self, message: str, context: dict) -> Optional[dict]:
        """Attempt to detect the relevant domain from the message."""
        domain_id = context.get("domain_id") or context.get("industry_domain")
        if domain_id:
            return self.domain_manager.get_profile(domain_id)

        profile = self.domain_manager.get_profile_by_name(message)
        return profile

    @staticmethod
    def _extract_company_names(message: str, context: dict) -> list[str]:
        """Extract company names from message and context."""
        companies = context.get("companies", [])
        if not companies:
            words = message.split()
            companies = [w for w in words if w[0].isupper() and len(w) > 2] if words else []
        if not companies:
            companies = [message]
        return companies[:10]

    @staticmethod
    def _extract_keywords(message: str) -> list[str]:
        """Extract relevant keywords from a message."""
        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "can", "shall",
            "for", "and", "nor", "but", "or", "yet", "so", "in", "on",
            "at", "to", "of", "by", "with", "from", "about", "what",
            "which", "who", "whom", "this", "that", "these", "those",
            "i", "me", "my", "we", "our", "you", "your", "he", "she",
            "it", "they", "them", "their", "trend", "trends", "monitor",
            "monitoring", "show", "tell", "give", "find", "search",
            "analyze", "analyse", "please",
        }
        words = message.lower().split()
        keywords = [w.strip(".,!?;:") for w in words if w.lower() not in stop_words and len(w) > 2]
        return keywords[:10] if keywords else ["market trends"]

    def _format_domains_response(self) -> str:
        """Format the list of available domains as a readable string."""
        domains = self.list_domains()
        lines = ["Available Industry Domain Profiles:\n"]
        for d in domains:
            lines.append(f"- **{d['name']}** (`{d['id']}`): {d['description']}")
        return "\n".join(lines)

    @staticmethod
    def _format_response(result: dict) -> str:
        """Format an analysis result dict as a readable string."""
        import json
        if isinstance(result, dict):
            analysis = result.get("analysis", result)
            if isinstance(analysis, dict):
                return json.dumps(analysis, indent=2, default=str)
            return str(analysis)
        return str(result)

    @staticmethod
    def _format_data_for_prompt(data_parts: list[dict]) -> str:
        """Format gathered data for inclusion in an LLM prompt."""
        sections = []
        for part in data_parts:
            source = part["source"]
            data = part["data"]
            if source == "news" and isinstance(data, list):
                headlines = [a.get("title", "") for a in data[:5] if a.get("title")]
                if headlines:
                    sections.append(
                        "Recent news:\n" + "\n".join(f"- {h}" for h in headlines)
                    )
            elif source == "wikipedia" and isinstance(data, list):
                for item in data[:2]:
                    extract = item.get("extract", "")
                    if extract:
                        sections.append(f"Background ({item.get('title', '')}):\n{extract[:400]}")
            elif source == "google_trends" and isinstance(data, dict):
                top = data.get("top", [])[:5]
                rising = data.get("rising", [])[:5]
                if top:
                    queries = [q.get("query", "") for q in top if q.get("query")]
                    sections.append(f"Top related searches: {', '.join(queries)}")
                if rising:
                    queries = [q.get("query", "") for q in rising if q.get("query")]
                    sections.append(f"Rising searches: {', '.join(queries)}")
        return "\n\n".join(sections) if sections else ""

    @staticmethod
    def _build_market_research_prompt(
        query: str, context: dict, enrichment: str, domain_profile: Optional[dict]
    ) -> str:
        """Build an enriched market research prompt."""
        domain_info = ""
        if domain_profile:
            kpis = domain_profile.get("kpis", [])
            if kpis:
                kpi_names = [k["full_name"] for k in kpis[:5]]
                domain_info = f"\nRelevant KPIs for this industry: {', '.join(kpi_names)}"

        return f"""Conduct comprehensive market research on the following topic:

Query: {query}
Context: {context}

{enrichment}
{domain_info}

Provide:
1. Market overview and size
2. Key trends and growth drivers
3. Major players and market share
4. Opportunities and challenges
5. Relevant data points and statistics

Include citations where possible. Format as a structured analysis."""

    async def _call_llm(self, prompt: str) -> str:
        """Call the LLM with a prompt."""
        if self.llm:
            try:
                messages = [
                    {"role": "system", "content": "You are a business analysis expert."},
                    {"role": "user", "content": prompt},
                ]
                return await self.llm.generate(messages)
            except Exception as e:
                return f"[Analysis Error: {str(e)}]"
        return (
            "[Demo Mode] Business analysis would be generated here. "
            "Configure OPENAI_API_KEY to enable full analysis capabilities."
        )
