"""
Tests for Domain Profiles and Trend Monitor

Covers DomainProfileManager and TrendMonitor with mocked dependencies.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.modules.business_analysis.domains import DomainProfileManager, DOMAIN_PROFILES
from app.modules.business_analysis.trend_monitor import TrendMonitor


# =========================================================================
# Domain Profile Manager Tests
# =========================================================================

class TestDomainProfileManager:
    """Tests for the DomainProfileManager."""

    def test_init_default(self):
        mgr = DomainProfileManager()
        assert len(mgr.list_domains()) == 7

    def test_init_with_custom(self):
        custom = {
            "custom_domain": {
                "id": "custom_domain",
                "name": "Custom Domain",
                "description": "A custom test domain",
            }
        }
        mgr = DomainProfileManager(custom_profiles=custom)
        assert len(mgr.list_domains()) == 8

    def test_list_domains(self):
        mgr = DomainProfileManager()
        domains = mgr.list_domains()
        assert isinstance(domains, list)
        for d in domains:
            assert "id" in d
            assert "name" in d
            assert "description" in d

    def test_all_seven_domains_present(self):
        mgr = DomainProfileManager()
        ids = mgr.get_all_domain_ids()
        expected = [
            "tech_saas", "ecommerce_retail", "healthcare",
            "finance_fintech", "real_estate", "education",
            "travel_hospitality",
        ]
        for domain_id in expected:
            assert domain_id in ids, f"Missing domain: {domain_id}"

    def test_get_profile(self):
        mgr = DomainProfileManager()
        profile = mgr.get_profile("tech_saas")
        assert profile is not None
        assert profile["name"] == "Tech / SaaS"
        assert "kpis" in profile
        assert "typical_competitors" in profile
        assert "swot_factors" in profile
        assert "pestel_factors" in profile
        assert "persona_templates" in profile
        assert "trend_keywords" in profile
        assert "research_parameters" in profile

    def test_get_profile_not_found(self):
        mgr = DomainProfileManager()
        assert mgr.get_profile("nonexistent") is None

    def test_get_profile_by_name(self):
        mgr = DomainProfileManager()
        profile = mgr.get_profile_by_name("healthcare")
        assert profile is not None
        assert profile["id"] == "healthcare"

    def test_get_profile_by_name_partial(self):
        mgr = DomainProfileManager()
        profile = mgr.get_profile_by_name("SaaS")
        assert profile is not None
        assert profile["id"] == "tech_saas"

    def test_get_profile_by_name_case_insensitive(self):
        mgr = DomainProfileManager()
        profile = mgr.get_profile_by_name("FINTECH")
        assert profile is not None
        assert profile["id"] == "finance_fintech"

    def test_get_profile_by_name_not_found(self):
        mgr = DomainProfileManager()
        assert mgr.get_profile_by_name("xyz_nonexistent") is None

    def test_get_profile_by_name_description_match(self):
        mgr = DomainProfileManager()
        profile = mgr.get_profile_by_name("telemedicine")
        assert profile is not None
        assert profile["id"] == "healthcare"

    def test_get_research_keywords(self):
        mgr = DomainProfileManager()
        keywords = mgr.get_research_keywords("tech_saas")
        assert isinstance(keywords, list)
        assert len(keywords) > 0
        assert "SaaS" in keywords

    def test_get_research_keywords_not_found(self):
        mgr = DomainProfileManager()
        assert mgr.get_research_keywords("nonexistent") == []

    def test_get_kpis(self):
        mgr = DomainProfileManager()
        kpis = mgr.get_kpis("ecommerce_retail")
        assert isinstance(kpis, list)
        assert len(kpis) > 0
        kpi_names = [k["name"] for k in kpis]
        assert "GMV" in kpi_names or "AOV" in kpi_names

    def test_get_kpis_not_found(self):
        mgr = DomainProfileManager()
        assert mgr.get_kpis("nonexistent") == []

    def test_get_typical_competitors(self):
        mgr = DomainProfileManager()
        comps = mgr.get_typical_competitors("finance_fintech")
        assert isinstance(comps, list)
        assert len(comps) > 0
        assert "Stripe" in comps or "PayPal" in comps

    def test_get_typical_competitors_not_found(self):
        mgr = DomainProfileManager()
        assert mgr.get_typical_competitors("nonexistent") == []

    def test_get_swot_factors(self):
        mgr = DomainProfileManager()
        swot = mgr.get_swot_factors("healthcare")
        assert "typical_strengths" in swot
        assert "typical_weaknesses" in swot
        assert "common_opportunities" in swot
        assert "known_threats" in swot
        assert len(swot["typical_strengths"]) > 0

    def test_get_swot_factors_not_found(self):
        mgr = DomainProfileManager()
        assert mgr.get_swot_factors("nonexistent") == {}

    def test_get_pestel_factors(self):
        mgr = DomainProfileManager()
        pestel = mgr.get_pestel_factors("real_estate")
        for key in ["political", "economic", "social", "technological", "environmental", "legal"]:
            assert key in pestel
            assert len(pestel[key]) > 0

    def test_get_pestel_factors_not_found(self):
        mgr = DomainProfileManager()
        assert mgr.get_pestel_factors("nonexistent") == {}

    def test_get_persona_templates(self):
        mgr = DomainProfileManager()
        templates = mgr.get_persona_templates("education")
        assert isinstance(templates, list)
        assert len(templates) > 0
        for t in templates:
            assert "archetype" in t
            assert "focus" in t

    def test_get_persona_templates_not_found(self):
        mgr = DomainProfileManager()
        assert mgr.get_persona_templates("nonexistent") == []

    def test_get_trend_keywords(self):
        mgr = DomainProfileManager()
        keywords = mgr.get_trend_keywords("travel_hospitality")
        assert isinstance(keywords, list)
        assert len(keywords) > 0

    def test_get_trend_keywords_not_found(self):
        mgr = DomainProfileManager()
        assert mgr.get_trend_keywords("nonexistent") == []

    def test_add_custom_profile(self):
        mgr = DomainProfileManager()
        initial_count = len(mgr.list_domains())
        mgr.add_custom_profile("gaming", {
            "name": "Gaming",
            "description": "Video game industry",
            "kpis": [{"name": "DAU", "full_name": "Daily Active Users"}],
        })
        assert len(mgr.list_domains()) == initial_count + 1
        profile = mgr.get_profile("gaming")
        assert profile["name"] == "Gaming"
        assert profile["id"] == "gaming"

    def test_remove_profile(self):
        mgr = DomainProfileManager()
        initial_count = len(mgr.list_domains())
        assert mgr.remove_profile("tech_saas") is True
        assert len(mgr.list_domains()) == initial_count - 1
        assert mgr.get_profile("tech_saas") is None

    def test_remove_profile_not_found(self):
        mgr = DomainProfileManager()
        assert mgr.remove_profile("nonexistent") is False

    def test_get_all_domain_ids(self):
        mgr = DomainProfileManager()
        ids = mgr.get_all_domain_ids()
        assert isinstance(ids, list)
        assert len(ids) == 7

    @pytest.mark.parametrize("domain_id", list(DOMAIN_PROFILES.keys()))
    def test_each_domain_has_required_fields(self, domain_id):
        """Validate that every domain profile has all required fields."""
        mgr = DomainProfileManager()
        profile = mgr.get_profile(domain_id)
        assert profile is not None

        required_keys = [
            "id", "name", "description", "research_parameters",
            "kpis", "typical_competitors", "swot_factors",
            "pestel_factors", "persona_templates", "trend_keywords",
        ]
        for key in required_keys:
            assert key in profile, f"Domain '{domain_id}' missing key: {key}"

        # Validate research_parameters sub-keys
        rp = profile["research_parameters"]
        for sub_key in ["search_keywords", "news_categories", "trends_timeframe"]:
            assert sub_key in rp, f"Domain '{domain_id}' research_parameters missing: {sub_key}"

        # Validate SWOT factors sub-keys
        swot = profile["swot_factors"]
        for sub_key in ["typical_strengths", "typical_weaknesses", "common_opportunities", "known_threats"]:
            assert sub_key in swot, f"Domain '{domain_id}' swot_factors missing: {sub_key}"
            assert len(swot[sub_key]) >= 3, f"Domain '{domain_id}' {sub_key} has fewer than 3 items"

        # Validate PESTEL factors sub-keys
        pestel = profile["pestel_factors"]
        for sub_key in ["political", "economic", "social", "technological", "environmental", "legal"]:
            assert sub_key in pestel, f"Domain '{domain_id}' pestel_factors missing: {sub_key}"
            assert len(pestel[sub_key]) >= 2, f"Domain '{domain_id}' {sub_key} has fewer than 2 items"

        # Validate KPIs
        assert len(profile["kpis"]) >= 5, f"Domain '{domain_id}' has fewer than 5 KPIs"
        for kpi in profile["kpis"]:
            assert "name" in kpi
            assert "full_name" in kpi

        # Validate competitors
        assert len(profile["typical_competitors"]) >= 5

        # Validate persona templates
        assert len(profile["persona_templates"]) >= 3


# =========================================================================
# Trend Monitor Tests
# =========================================================================

class TestTrendMonitor:
    """Tests for the TrendMonitor."""

    def setup_method(self):
        self.mock_llm = AsyncMock()
        self.mock_news = MagicMock()
        self.mock_news.is_configured = False
        self.mock_trends = AsyncMock()
        self.mock_wiki = AsyncMock()
        self.mock_scraper = AsyncMock()
        self.monitor = TrendMonitor(
            llm_client=self.mock_llm,
            news_client=self.mock_news,
            trends_client=self.mock_trends,
            wikipedia_client=self.mock_wiki,
            web_scraper=self.mock_scraper,
        )

    @pytest.mark.asyncio
    async def test_monitor_trends_basic(self):
        self.mock_llm.generate.return_value = json.dumps({
            "industry": "Tech",
            "executive_summary": "Tech is growing.",
            "trending_topics": [],
            "emerging_signals": [],
            "news_themes": [],
            "competitive_signals": [],
            "recommendations": [],
            "risk_alerts": [],
        })
        self.mock_trends.get_interest_over_time.return_value = {"data": []}
        self.mock_trends.get_related_queries.return_value = {"top": [], "rising": []}

        result = await self.monitor.monitor_trends(
            keywords=["AI", "machine learning"],
            industry="Tech",
        )

        assert "analysis" in result
        assert result["type"] == "trend_monitoring"
        assert "metadata" in result["analysis"]

    @pytest.mark.asyncio
    async def test_monitor_trends_fallback(self):
        monitor = TrendMonitor(llm_client=None)
        result = await monitor.monitor_trends(
            keywords=["test"],
            industry="General",
        )

        assert result["type"] == "trend_monitoring"
        assert "Demo Mode" in result["analysis"]["executive_summary"]

    @pytest.mark.asyncio
    async def test_get_trending_now(self):
        self.mock_trends.get_trending_searches.return_value = ["topic1", "topic2"]

        result = await self.monitor.get_trending_now(industry="Tech")

        assert "trending_searches" in result
        assert "industry_news" in result
        assert result["industry"] == "Tech"

    @pytest.mark.asyncio
    async def test_compare_trend_keywords(self):
        self.mock_trends.get_interest_over_time.return_value = {
            "data": [
                {"date": "2025-01-01", "AI": 80, "ML": 60},
                {"date": "2025-02-01", "AI": 85, "ML": 65},
                {"date": "2025-03-01", "AI": 90, "ML": 70},
            ],
            "keywords": ["AI", "ML"],
        }
        self.mock_trends.get_interest_by_region.return_value = {}

        result = await self.monitor.compare_trend_keywords(
            keywords=["AI", "ML"],
            timeframe="today 3-m",
        )

        assert "keyword_stats" in result
        assert "ranking" in result
        assert result["ranking"][0]["keyword"] == "AI"
        assert result["ranking"][0]["rank"] == 1

    @pytest.mark.asyncio
    async def test_compare_keywords_no_trends_client(self):
        monitor = TrendMonitor(llm_client=None)
        result = await monitor.compare_trend_keywords(["test"])
        assert "error" in result

    @pytest.mark.asyncio
    async def test_detect_anomalies(self):
        data = [{"date": f"2025-01-{i+1:02d}", "AI": 50} for i in range(20)]
        data[10]["AI"] = 200  # spike
        data[15]["AI"] = 5    # drop

        self.mock_trends.get_interest_over_time.return_value = {
            "data": data,
            "keywords": ["AI"],
        }

        result = await self.monitor.detect_anomalies(
            keywords=["AI"],
            timeframe="today 3-m",
            threshold=1.5,
        )

        assert "anomalies" in result
        assert result["total_anomalies"] >= 1
        spike = [a for a in result["anomalies"] if a["type"] == "spike"]
        assert len(spike) >= 1

    @pytest.mark.asyncio
    async def test_detect_anomalies_no_client(self):
        monitor = TrendMonitor(llm_client=None)
        result = await monitor.detect_anomalies(["test"])
        assert "error" in result

    @pytest.mark.asyncio
    async def test_generate_trend_report(self):
        self.mock_llm.generate.return_value = json.dumps({
            "industry": "Tech",
            "executive_summary": "Growing.",
            "trending_topics": [],
            "emerging_signals": [],
            "news_themes": [],
            "competitive_signals": [],
            "recommendations": [],
            "risk_alerts": [],
        })
        self.mock_trends.get_interest_over_time.return_value = {"data": []}
        self.mock_trends.get_related_queries.return_value = {"top": [], "rising": []}

        domain_profile = {
            "name": "Tech / SaaS",
            "trend_keywords": ["SaaS", "cloud"],
            "typical_competitors": ["Salesforce", "HubSpot"],
        }

        result = await self.monitor.generate_trend_report(
            industry="Tech",
            domain_profile=domain_profile,
        )

        assert result["report_type"] == "comprehensive_trend_report"
        assert result["industry"] == "Tech"
        assert result["domain_profile_used"] == "Tech / SaaS"

    def test_timeframe_to_readable(self):
        assert TrendMonitor._timeframe_to_readable("today 12-m") == "Last 12 months"
        assert TrendMonitor._timeframe_to_readable("now 7-d") == "Last 7 days"
        assert TrendMonitor._timeframe_to_readable("custom") == "custom"

    def test_industry_to_news_category(self):
        assert TrendMonitor._industry_to_news_category("tech startup") == "technology"
        assert TrendMonitor._industry_to_news_category("healthcare AI") == "health"
        assert TrendMonitor._industry_to_news_category("fintech") == "technology"
        assert TrendMonitor._industry_to_news_category("unknown") == "business"

    def test_calculate_trend(self):
        assert TrendMonitor._calculate_trend([10, 20, 30, 40, 50]) == "rising"
        assert TrendMonitor._calculate_trend([50, 40, 30, 20, 10]) == "declining"
        assert TrendMonitor._calculate_trend([50, 50, 50, 50, 50]) == "stable"
        assert TrendMonitor._calculate_trend([50]) == "insufficient_data"

    def test_get_available_sources(self):
        sources = self.monitor._get_available_sources()
        assert "google_trends" in sources
        assert "wikipedia" in sources
        assert "web_scraper" in sources
        assert "news_api" not in sources  # is_configured = False

    def test_get_available_sources_with_news(self):
        self.mock_news.is_configured = True
        sources = self.monitor._get_available_sources()
        assert "news_api" in sources

    def test_build_fallback_analysis(self):
        result = TrendMonitor._build_fallback_analysis(["AI"], "Tech")
        assert "Demo Mode" in result["executive_summary"]
        assert result["industry"] == "Tech"

    def test_extract_insights_rising(self):
        analysis = {
            "trending_topics": [
                {"topic": "AI", "direction": "rising"},
                {"topic": "Blockchain", "direction": "stable"},
            ],
            "risk_alerts": [
                {"risk": "Regulation", "severity": "critical"},
            ],
            "emerging_signals": [
                {"signal": "Quantum", "potential_impact": "high"},
            ],
        }
        insights = TrendMonitor._extract_insights(analysis)
        assert len(insights) == 3
        rising = [i for i in insights if i["type"] == "rising_trends"]
        assert rising[0]["count"] == 1

    def test_extract_insights_empty(self):
        analysis = {
            "trending_topics": [],
            "risk_alerts": [],
            "emerging_signals": [],
        }
        insights = TrendMonitor._extract_insights(analysis)
        assert len(insights) == 0

    def test_parse_json_response_valid(self):
        result = TrendMonitor._parse_json_response('{"key": "value"}')
        assert result == {"key": "value"}

    def test_parse_json_response_markdown(self):
        result = TrendMonitor._parse_json_response('```json\n{"key": "value"}\n```')
        assert result == {"key": "value"}

    def test_parse_json_response_invalid(self):
        result = TrendMonitor._parse_json_response("not json")
        assert result is None

    def test_parse_json_response_empty(self):
        result = TrendMonitor._parse_json_response("")
        assert result is None
