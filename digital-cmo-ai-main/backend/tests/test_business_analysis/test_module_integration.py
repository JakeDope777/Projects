"""
Integration Tests for BusinessAnalysisModule

Tests the main module orchestration, routing, and integration
of all sub-modules.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.modules.business_analysis.module import BusinessAnalysisModule


class TestBusinessAnalysisModuleInit:
    """Tests for module initialisation."""

    def test_init_default(self):
        module = BusinessAnalysisModule()
        assert module.llm is None
        assert module.memory is None
        assert module.news_client is not None
        assert module.trends_client is not None
        assert module.wikipedia_client is not None
        assert module.web_scraper is not None
        assert module.swot_pestel is not None
        assert module.competitor_analyzer is not None
        assert module.persona_generator is not None
        assert module.trend_monitor is not None
        assert module.domain_manager is not None

    def test_init_with_llm(self):
        mock_llm = AsyncMock()
        module = BusinessAnalysisModule(llm_client=mock_llm)
        assert module.llm is mock_llm

    def test_init_with_news_api_key(self):
        module = BusinessAnalysisModule(news_api_key="test-key")
        assert module.news_client.is_configured is True

    def test_domain_manager_available(self):
        module = BusinessAnalysisModule()
        domains = module.list_domains()
        assert len(domains) == 7


class TestBusinessAnalysisModuleRouting:
    """Tests for the handle() routing logic."""

    def setup_method(self):
        self.mock_llm = AsyncMock()
        self.module = BusinessAnalysisModule(llm_client=self.mock_llm)

    @pytest.mark.asyncio
    async def test_route_swot(self):
        self.mock_llm.generate.return_value = json.dumps({
            "subject": "TestCo",
            "summary": "Good company.",
            "strengths": [], "weaknesses": [],
            "opportunities": [], "threats": [],
            "cross_analysis": {
                "so_strategies": [], "wo_strategies": [],
                "st_strategies": [], "wt_strategies": [],
            },
            "priority_actions": [],
        })

        result = await self.module.handle(
            "Generate a SWOT analysis for TestCo",
            context={},
        )

        assert "response" in result
        assert isinstance(result["response"], str)

    @pytest.mark.asyncio
    async def test_route_pestel(self):
        self.mock_llm.generate.return_value = json.dumps({
            "subject": "TestCo",
            "summary": "Complex environment.",
            "political": [], "economic": [], "social": [],
            "technological": [], "environmental": [], "legal": [],
            "risk_matrix": {
                "high_impact_high_likelihood": [],
                "high_impact_low_likelihood": [],
                "low_impact_high_likelihood": [],
                "low_impact_low_likelihood": [],
            },
            "strategic_recommendations": [],
        })

        result = await self.module.handle(
            "Create a PESTEL analysis for the fintech industry",
            context={},
        )

        assert "response" in result

    @pytest.mark.asyncio
    async def test_route_persona(self):
        self.mock_llm.generate.return_value = json.dumps({
            "subject": "TestProduct",
            "methodology": "market-research",
            "personas": [{
                "id": "p1", "name": "Alex", "title": "The Buyer",
                "demographics": {}, "professional": {},
                "goals_and_motivations": [], "pain_points": [],
                "buying_behavior": {},
            }],
            "persona_comparison": {
                "key_differences": [], "common_threads": [], "coverage_gaps": [],
            },
            "targeting_recommendations": [],
        })

        result = await self.module.handle(
            "Generate buyer persona for our SaaS product",
            context={},
        )

        assert "response" in result

    @pytest.mark.asyncio
    async def test_route_competitor(self):
        self.mock_llm.generate.return_value = json.dumps({
            "analysis_date": "2025-01-01",
            "industry": "Tech",
            "competitors": [{"name": "CompA", "overview": "A company"}],
            "comparison_matrix": {"dimensions": [], "ratings": {}},
            "competitive_landscape": {
                "market_leaders": [], "challengers": [],
                "niche_players": [], "emerging_threats": [],
            },
            "strategic_recommendations": [],
            "gaps_and_opportunities": [],
        })

        result = await self.module.handle(
            "Analyze competitor Salesforce in the CRM market",
            context={"companies": ["Salesforce"]},
        )

        assert "response" in result

    @pytest.mark.asyncio
    async def test_route_trends(self):
        self.mock_llm.generate.return_value = json.dumps({
            "industry": "Tech",
            "executive_summary": "Growing.",
            "trending_topics": [], "emerging_signals": [],
            "news_themes": [], "competitive_signals": [],
            "recommendations": [], "risk_alerts": [],
        })

        result = await self.module.handle(
            "Show me the latest trends in AI",
            context={},
        )

        assert "response" in result

    @pytest.mark.asyncio
    async def test_route_domains(self):
        result = await self.module.handle(
            "List available domain profiles",
            context={},
        )

        assert "response" in result
        assert "Tech / SaaS" in result["response"]
        assert "Healthcare" in result["response"]

    @pytest.mark.asyncio
    async def test_route_market_research_default(self):
        self.mock_llm.generate.return_value = "Market analysis for cloud computing..."

        result = await self.module.handle(
            "Tell me about the cloud computing market",
            context={},
        )

        assert "response" in result

    @pytest.mark.asyncio
    async def test_domain_detection_from_context(self):
        result = await self.module.handle(
            "List available domain profiles",
            context={"domain_id": "tech_saas"},
        )

        assert "response" in result


class TestBusinessAnalysisModuleAPIs:
    """Tests for the public API methods."""

    def setup_method(self):
        self.module = BusinessAnalysisModule()

    @pytest.mark.asyncio
    async def test_analyze_market_no_llm(self):
        result = await self.module.analyze_market("cloud computing trends")
        assert "insights" in result
        assert "sources" in result
        assert "analysis" in result

    @pytest.mark.asyncio
    async def test_generate_swot_no_llm(self):
        result = await self.module.generate_swot("TestCo", "Tech")
        assert result["type"] == "swot"

    @pytest.mark.asyncio
    async def test_generate_pestel_no_llm(self):
        result = await self.module.generate_pestel("TestCo", "Tech")
        assert result["type"] == "pestel"

    @pytest.mark.asyncio
    async def test_generate_combined_no_llm(self):
        result = await self.module.generate_combined_analysis("TestCo", "Tech")
        assert "swot" in result
        assert "pestel" in result

    @pytest.mark.asyncio
    async def test_analyze_competitors_no_llm(self):
        result = await self.module.analyze_competitors(["CompA", "CompB"])
        assert result["type"] == "competitor_analysis"

    @pytest.mark.asyncio
    async def test_create_personas_no_llm(self):
        result = await self.module.create_personas(
            subject="TestProduct",
            num_personas=2,
        )
        assert result["type"] == "persona_generation"

    @pytest.mark.asyncio
    async def test_monitor_trends_no_llm(self):
        result = await self.module.monitor_trends(
            keywords=["AI"],
            industry="Tech",
        )
        assert result["type"] == "trend_monitoring"

    def test_list_domains(self):
        domains = self.module.list_domains()
        assert len(domains) == 7

    def test_get_domain_profile(self):
        profile = self.module.get_domain_profile("tech_saas")
        assert profile is not None
        assert profile["name"] == "Tech / SaaS"

    def test_get_domain_kpis(self):
        kpis = self.module.get_domain_kpis("ecommerce_retail")
        assert len(kpis) > 0


class TestBusinessAnalysisModuleHelpers:
    """Tests for private helper methods."""

    def test_extract_keywords(self):
        keywords = BusinessAnalysisModule._extract_keywords(
            "Show me the latest trends in artificial intelligence"
        )
        assert "artificial" in keywords or "intelligence" in keywords
        assert "the" not in keywords
        assert "show" not in keywords

    def test_extract_keywords_empty(self):
        keywords = BusinessAnalysisModule._extract_keywords("the a an")
        assert keywords == ["market trends"]

    def test_extract_company_names_from_context(self):
        companies = BusinessAnalysisModule._extract_company_names(
            "analyze competitors",
            {"companies": ["Google", "Microsoft"]},
        )
        assert companies == ["Google", "Microsoft"]

    def test_extract_company_names_from_message(self):
        companies = BusinessAnalysisModule._extract_company_names(
            "Compare Google and Microsoft",
            {},
        )
        assert "Google" in companies
        assert "Microsoft" in companies

    def test_format_response_dict(self):
        result = {"key": "value", "nested": {"a": 1}}
        formatted = BusinessAnalysisModule._format_response(result)
        assert isinstance(formatted, str)
        parsed = json.loads(formatted)
        assert parsed["key"] == "value"

    def test_format_response_string(self):
        result = "plain text"
        formatted = BusinessAnalysisModule._format_response(result)
        assert formatted == "plain text"

    def test_format_data_for_prompt_news(self):
        data_parts = [
            {
                "source": "news",
                "data": [
                    {"title": "AI is growing", "url": "https://example.com"},
                    {"title": "Cloud computing trends", "url": "https://example.com/2"},
                ],
            }
        ]
        result = BusinessAnalysisModule._format_data_for_prompt(data_parts)
        assert "AI is growing" in result
        assert "Cloud computing trends" in result

    def test_format_data_for_prompt_wikipedia(self):
        data_parts = [
            {
                "source": "wikipedia",
                "data": [
                    {"title": "AI", "extract": "Artificial intelligence is..."},
                ],
            }
        ]
        result = BusinessAnalysisModule._format_data_for_prompt(data_parts)
        assert "Artificial intelligence" in result

    def test_format_data_for_prompt_trends(self):
        data_parts = [
            {
                "source": "google_trends",
                "data": {
                    "top": [{"query": "AI tools"}],
                    "rising": [{"query": "ChatGPT"}],
                },
            }
        ]
        result = BusinessAnalysisModule._format_data_for_prompt(data_parts)
        assert "AI tools" in result
        assert "ChatGPT" in result

    def test_format_data_for_prompt_empty(self):
        result = BusinessAnalysisModule._format_data_for_prompt([])
        assert result == ""

    def test_format_domains_response(self):
        module = BusinessAnalysisModule()
        response = module._format_domains_response()
        assert "Tech / SaaS" in response
        assert "Healthcare" in response
        assert "E-commerce" in response
