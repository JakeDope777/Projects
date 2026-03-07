"""
Tests for Business Analysis Engines

Covers SWOT/PESTEL analyzer, Competitor analyzer, and Persona generator
with mocked LLM and data source calls.
"""

import json
import pytest
import numpy as np
from unittest.mock import AsyncMock, MagicMock, patch

from app.modules.business_analysis.swot_pestel import SWOTPESTELAnalyzer
from app.modules.business_analysis.competitor_analysis import CompetitorAnalyzer
from app.modules.business_analysis.persona_generator import PersonaGenerator


# =========================================================================
# SWOT/PESTEL Analyzer Tests
# =========================================================================

class TestSWOTPESTELAnalyzer:
    """Tests for the SWOTPESTELAnalyzer."""

    def setup_method(self):
        self.mock_llm = AsyncMock()
        self.mock_news = MagicMock()
        self.mock_news.is_configured = False
        self.mock_trends = AsyncMock()
        self.mock_wiki = AsyncMock()
        self.analyzer = SWOTPESTELAnalyzer(
            llm_client=self.mock_llm,
            news_client=self.mock_news,
            trends_client=self.mock_trends,
            wikipedia_client=self.mock_wiki,
        )

    @pytest.mark.asyncio
    async def test_generate_swot_with_llm(self):
        swot_response = json.dumps({
            "subject": "TestCo",
            "industry": "Tech",
            "summary": "TestCo is a strong player.",
            "strengths": [
                {"factor": "Strong brand", "impact": "high", "confidence": "high",
                 "evidence": "Market leader", "recommendations": ["Expand"]}
            ],
            "weaknesses": [
                {"factor": "High costs", "impact": "medium", "confidence": "medium",
                 "evidence": "Above industry avg", "recommendations": ["Optimise"]}
            ],
            "opportunities": [
                {"factor": "New market", "impact": "high", "confidence": "medium",
                 "evidence": "Growing demand", "recommendations": ["Enter market"]}
            ],
            "threats": [
                {"factor": "Competition", "impact": "high", "confidence": "high",
                 "evidence": "New entrants", "recommendations": ["Differentiate"]}
            ],
            "cross_analysis": {
                "so_strategies": ["Leverage brand to enter new market"],
                "wo_strategies": ["Reduce costs to compete"],
                "st_strategies": ["Use brand to fend off competition"],
                "wt_strategies": ["Cut costs and focus on core"]
            },
            "priority_actions": ["Enter new market", "Reduce costs"]
        })
        self.mock_llm.generate.return_value = swot_response
        self.mock_trends.get_related_queries.return_value = {"top": [], "rising": []}
        self.mock_wiki.get_summary.return_value = {"extract": ""}

        result = await self.analyzer.generate_swot(
            subject="TestCo",
            industry="Tech",
            enrich_with_data=False,
        )

        assert result["type"] == "swot"
        assert "analysis" in result
        analysis = result["analysis"]
        assert len(analysis["strengths"]) >= 1
        assert analysis["strengths"][0]["impact"] == "high"
        assert "metadata" in analysis

    @pytest.mark.asyncio
    async def test_generate_swot_fallback_no_llm(self):
        analyzer = SWOTPESTELAnalyzer(llm_client=None)
        result = await analyzer.generate_swot(
            subject="TestCo",
            industry="Tech",
            enrich_with_data=False,
        )

        assert result["type"] == "swot"
        analysis = result["analysis"]
        assert "Demo Mode" in analysis["summary"]
        assert analysis["metadata"]["model"] == "demo"

    @pytest.mark.asyncio
    async def test_generate_pestel_with_llm(self):
        pestel_response = json.dumps({
            "subject": "TestCo",
            "industry": "Tech",
            "summary": "Complex regulatory environment.",
            "political": [
                {"factor": "New regulations", "impact": "high", "likelihood": "high",
                 "timeframe": "short-term", "evidence": "Proposed bill",
                 "implications": ["Compliance costs"]}
            ],
            "economic": [
                {"factor": "Recession risk", "impact": "medium", "likelihood": "medium",
                 "timeframe": "medium-term", "evidence": "Economic indicators",
                 "implications": ["Reduced spending"]}
            ],
            "social": [],
            "technological": [],
            "environmental": [],
            "legal": [],
            "risk_matrix": {
                "high_impact_high_likelihood": ["New regulations"],
                "high_impact_low_likelihood": [],
                "low_impact_high_likelihood": [],
                "low_impact_low_likelihood": []
            },
            "strategic_recommendations": ["Prepare for compliance"]
        })
        self.mock_llm.generate.return_value = pestel_response
        self.mock_trends.get_related_queries.return_value = {"top": [], "rising": []}
        self.mock_wiki.get_summary.return_value = {"extract": ""}

        result = await self.analyzer.generate_pestel(
            subject="TestCo",
            industry="Tech",
            enrich_with_data=False,
        )

        assert result["type"] == "pestel"
        analysis = result["analysis"]
        assert len(analysis["political"]) >= 1
        assert analysis["political"][0]["impact"] == "high"

    @pytest.mark.asyncio
    async def test_generate_pestel_fallback_no_llm(self):
        analyzer = SWOTPESTELAnalyzer(llm_client=None)
        result = await analyzer.generate_pestel(
            subject="TestCo",
            enrich_with_data=False,
        )

        assert result["type"] == "pestel"
        analysis = result["analysis"]
        assert "Demo Mode" in analysis["summary"]

    @pytest.mark.asyncio
    async def test_generate_combined(self):
        self.mock_llm.generate.return_value = json.dumps(
            self.analyzer._build_fallback_swot("TestCo", "Tech")
        )
        self.mock_trends.get_related_queries.return_value = {"top": [], "rising": []}
        self.mock_wiki.get_summary.return_value = {"extract": ""}

        result = await self.analyzer.generate_combined(
            subject="TestCo",
            industry="Tech",
        )

        assert "swot" in result
        assert "pestel" in result
        assert "combined_insights" in result
        assert "total_factors_identified" in result["combined_insights"]

    @pytest.mark.asyncio
    async def test_swot_with_domain_profile(self):
        domain_profile = {
            "swot_factors": {
                "typical_strengths": ["Scalable infrastructure"],
                "typical_weaknesses": ["High CAC"],
                "common_opportunities": ["AI integration"],
                "known_threats": ["Open source competition"],
            }
        }
        self.mock_llm.generate.return_value = json.dumps(
            self.analyzer._build_fallback_swot("TestCo", "SaaS")
        )
        self.mock_trends.get_related_queries.return_value = {"top": [], "rising": []}
        self.mock_wiki.get_summary.return_value = {"extract": ""}

        result = await self.analyzer.generate_swot(
            subject="TestCo",
            industry="SaaS",
            domain_profile=domain_profile,
            enrich_with_data=False,
        )

        assert result["analysis"]["metadata"]["domain_profile_used"] is True

    def test_parse_json_response_valid(self):
        text = '{"key": "value"}'
        result = SWOTPESTELAnalyzer._parse_json_response(text)
        assert result == {"key": "value"}

    def test_parse_json_response_with_markdown(self):
        text = '```json\n{"key": "value"}\n```'
        result = SWOTPESTELAnalyzer._parse_json_response(text)
        assert result == {"key": "value"}

    def test_parse_json_response_embedded(self):
        text = 'Here is the analysis: {"key": "value"} end.'
        result = SWOTPESTELAnalyzer._parse_json_response(text)
        assert result == {"key": "value"}

    def test_parse_json_response_invalid(self):
        result = SWOTPESTELAnalyzer._parse_json_response("not json at all")
        assert result is None

    def test_parse_json_response_empty(self):
        result = SWOTPESTELAnalyzer._parse_json_response("")
        assert result is None

    def test_extract_insights_swot(self):
        analysis = {
            "strengths": [
                {"factor": "Strong brand", "impact": "high"},
                {"factor": "Good team", "impact": "medium"},
            ],
            "weaknesses": [{"factor": "High costs", "impact": "high"}],
            "opportunities": [],
            "threats": [{"factor": "Competition", "impact": "low"}],
        }
        insights = SWOTPESTELAnalyzer._extract_insights(analysis, "swot")
        assert len(insights) >= 1
        high_impact = [i for i in insights if i["category"] == "strengths"]
        assert high_impact[0]["high_impact_count"] == 1

    def test_count_factors(self):
        analysis = {
            "strengths": [1, 2, 3],
            "weaknesses": [1],
            "opportunities": [1, 2],
            "threats": [],
        }
        count = SWOTPESTELAnalyzer._count_factors(analysis, "swot")
        assert count == 6


# =========================================================================
# Competitor Analyzer Tests
# =========================================================================

class TestCompetitorAnalyzer:
    """Tests for the CompetitorAnalyzer."""

    def setup_method(self):
        self.mock_llm = AsyncMock()
        self.mock_news = MagicMock()
        self.mock_news.is_configured = False
        self.mock_wiki = AsyncMock()
        self.mock_scraper = AsyncMock()
        self.mock_trends = AsyncMock()
        self.analyzer = CompetitorAnalyzer(
            llm_client=self.mock_llm,
            news_client=self.mock_news,
            wikipedia_client=self.mock_wiki,
            web_scraper=self.mock_scraper,
            trends_client=self.mock_trends,
        )

    @pytest.mark.asyncio
    async def test_analyze_competitors_with_llm(self):
        response = json.dumps({
            "analysis_date": "2025-01-01",
            "industry": "Tech",
            "competitors": [
                {
                    "name": "CompA",
                    "overview": "A tech company",
                    "threat_level": "high",
                    "threat_reasoning": "Market leader",
                    "strengths": ["Innovation"],
                    "weaknesses": ["Expensive"],
                }
            ],
            "comparison_matrix": {"dimensions": ["Quality"], "ratings": {}},
            "competitive_landscape": {
                "market_leaders": ["CompA"],
                "challengers": [],
                "niche_players": [],
                "emerging_threats": [],
            },
            "strategic_recommendations": [
                {"recommendation": "Differentiate", "priority": "high", "rationale": "Key"}
            ],
            "gaps_and_opportunities": ["Underserved segment"],
        })
        self.mock_llm.generate.return_value = response
        self.mock_wiki.get_company_info.return_value = {"found": False}

        result = await self.analyzer.analyze_competitors(
            company_names=["CompA"],
            industry="Tech",
            enrich_with_data=False,
        )

        assert result["type"] == "competitor_analysis"
        assert len(result["analysis"]["competitors"]) == 1
        assert result["analysis"]["competitors"][0]["name"] == "CompA"

    @pytest.mark.asyncio
    async def test_analyze_competitors_fallback(self):
        analyzer = CompetitorAnalyzer(llm_client=None)
        result = await analyzer.analyze_competitors(
            company_names=["CompA", "CompB"],
            industry="Tech",
            enrich_with_data=False,
        )

        assert result["type"] == "competitor_analysis"
        assert len(result["analysis"]["competitors"]) == 2
        assert "Demo Mode" in result["analysis"]["competitors"][0]["overview"]

    @pytest.mark.asyncio
    async def test_quick_comparison(self):
        response = json.dumps({
            "matrix": {
                "CompA": {"Quality": {"score": 4, "notes": "Good"}},
                "CompB": {"Quality": {"score": 3, "notes": "Average"}},
            },
            "summary": "CompA leads in quality.",
            "winner_by_dimension": {"Quality": "CompA"},
        })
        self.mock_llm.generate.return_value = response

        result = await self.analyzer.quick_comparison(
            company_names=["CompA", "CompB"],
            dimensions=["Quality"],
        )

        assert "matrix" in result
        assert "metadata" in result

    @pytest.mark.asyncio
    async def test_research_company_with_wikipedia(self):
        self.mock_wiki.get_company_info.return_value = {
            "found": True,
            "summary": "A great company",
            "company": "TestCo",
        }
        self.mock_trends.get_interest_over_time.return_value = {"data": []}

        result = await self.analyzer.research_company("TestCo")

        assert result["company"] == "TestCo"
        assert "wikipedia" in result["sources_used"]

    @pytest.mark.asyncio
    async def test_track_competitors(self):
        analyzer = CompetitorAnalyzer(llm_client=None)
        result = await analyzer.track_competitors(
            company_names=["CompA", "CompB"],
            metrics=["news_mentions"],
        )

        assert "tracked_companies" in result
        assert len(result["tracked_companies"]) == 2
        assert "CompA" in result["snapshots"]
        assert "CompB" in result["snapshots"]

    def test_extract_insights(self):
        analysis = {
            "competitors": [
                {"name": "CompA", "threat_level": "high"},
                {"name": "CompB", "threat_level": "low"},
            ],
            "strategic_recommendations": [
                {"recommendation": "Act now", "priority": "high"},
            ],
            "gaps_and_opportunities": ["Gap 1"],
        }
        insights = CompetitorAnalyzer._extract_insights(analysis)
        assert len(insights) >= 1
        threat_insight = [i for i in insights if i["type"] == "high_threat_competitors"]
        assert len(threat_insight) == 1
        assert "CompA" in threat_insight[0]["companies"]


# =========================================================================
# Persona Generator Tests
# =========================================================================

class TestPersonaGenerator:
    """Tests for the PersonaGenerator."""

    def setup_method(self):
        self.mock_llm = AsyncMock()
        self.mock_trends = AsyncMock()
        self.mock_news = MagicMock()
        self.mock_news.is_configured = False
        self.generator = PersonaGenerator(
            llm_client=self.mock_llm,
            trends_client=self.mock_trends,
            news_client=self.mock_news,
        )

    @pytest.mark.asyncio
    async def test_generate_personas_with_llm(self):
        response = json.dumps({
            "subject": "TestProduct",
            "industry": "Tech",
            "methodology": "market-research",
            "personas": [
                {
                    "id": "persona_1",
                    "name": "Alex",
                    "title": "The Decision Maker",
                    "demographics": {"age_range": "35-45"},
                    "professional": {"job_title": "CTO"},
                    "goals_and_motivations": [{"goal": "Scale", "priority": "high"}],
                    "pain_points": [{"pain_point": "Complexity", "severity": "high"}],
                    "buying_behavior": {"research_channels": ["web"]},
                    "cluster_id": None,
                }
            ],
            "persona_comparison": {
                "key_differences": ["Role level"],
                "common_threads": ["Tech focus"],
                "coverage_gaps": ["SMB segment"],
            },
            "targeting_recommendations": [],
        })
        self.mock_llm.generate.return_value = response
        self.mock_trends.get_related_queries.return_value = {"top": [], "rising": []}

        result = await self.generator.generate_personas(
            subject="TestProduct",
            industry="Tech",
            num_personas=1,
        )

        assert result["type"] == "persona_generation"
        personas = result["personas"]
        assert len(personas["personas"]) == 1
        assert personas["personas"][0]["name"] == "Alex"

    @pytest.mark.asyncio
    async def test_generate_personas_fallback(self):
        generator = PersonaGenerator(llm_client=None)
        result = await generator.generate_personas(
            subject="TestProduct",
            num_personas=3,
        )

        assert result["type"] == "persona_generation"
        assert len(result["personas"]["personas"]) == 3

    @pytest.mark.asyncio
    async def test_num_personas_clamped(self):
        generator = PersonaGenerator(llm_client=None)

        # Test max clamp
        result = await generator.generate_personas(
            subject="Test", num_personas=10
        )
        assert len(result["personas"]["personas"]) <= 6

        # Test min clamp
        result = await generator.generate_personas(
            subject="Test", num_personas=0
        )
        assert len(result["personas"]["personas"]) >= 1

    def test_cluster_customers_basic(self):
        customer_data = [
            {"age": 25, "income": 50000, "segment": "A"},
            {"age": 26, "income": 52000, "segment": "A"},
            {"age": 45, "income": 90000, "segment": "B"},
            {"age": 46, "income": 92000, "segment": "B"},
            {"age": 35, "income": 70000, "segment": "C"},
            {"age": 36, "income": 72000, "segment": "C"},
        ]

        result = self.generator._cluster_customers(customer_data, 3)

        assert result["n_clusters"] == 3
        assert result["total_customers"] == 6
        assert len(result["clusters"]) == 3
        total_assigned = sum(c["size"] for c in result["clusters"])
        assert total_assigned == 6

    def test_cluster_customers_empty(self):
        result = self.generator._cluster_customers([], 3)
        assert result["n_clusters"] == 0

    def test_cluster_customers_fewer_than_k(self):
        data = [{"age": 25}, {"age": 30}]
        result = self.generator._cluster_customers(data, 5)
        assert result["n_clusters"] == 2

    def test_encode_features_numeric(self):
        data = [
            {"age": 25, "income": 50000},
            {"age": 35, "income": 70000},
            {"age": 45, "income": 90000},
        ]
        features, names = self.generator._encode_features(data)
        assert features.shape == (3, 2)
        assert "age" in names
        assert "income" in names

    def test_encode_features_categorical(self):
        data = [
            {"segment": "A", "age": 25},
            {"segment": "B", "age": 35},
            {"segment": "A", "age": 45},
        ]
        features, names = self.generator._encode_features(data)
        assert features.shape[0] == 3
        assert features.shape[1] >= 2  # age + at least one categorical column

    def test_encode_features_empty(self):
        features, names = self.generator._encode_features([])
        assert features.shape == (0,)

    def test_kmeans_basic(self):
        X = np.array([
            [0, 0], [1, 0], [0, 1],
            [10, 10], [11, 10], [10, 11],
        ], dtype=float)

        labels, centroids = PersonaGenerator._kmeans(X, k=2)

        assert len(labels) == 6
        assert centroids.shape == (2, 2)
        # Points in each group should share a label
        assert labels[0] == labels[1] == labels[2]
        assert labels[3] == labels[4] == labels[5]
        assert labels[0] != labels[3]

    def test_kmeans_single_cluster(self):
        X = np.array([[1, 1], [2, 2], [3, 3]], dtype=float)
        labels, centroids = PersonaGenerator._kmeans(X, k=1)
        assert all(l == 0 for l in labels)

    def test_kmeans_empty(self):
        X = np.array([]).reshape(0, 2)
        labels, centroids = PersonaGenerator._kmeans(X, k=2)
        assert len(labels) == 0

    def test_get_dominant_attributes(self):
        customers = [
            {"age": 25, "segment": "A"},
            {"age": 30, "segment": "A"},
            {"age": 35, "segment": "B"},
        ]
        result = PersonaGenerator._get_dominant_attributes(customers)
        assert "age" in result
        assert result["age"]["mean"] == 30.0
        assert "segment" in result
        assert result["segment"]["top_values"][0]["value"] == "A"

    def test_format_cluster_insights(self):
        cluster_result = {
            "clusters": [
                {
                    "cluster_id": 0,
                    "size": 10,
                    "percentage": 50.0,
                    "dominant_attributes": {
                        "age": {"mean": 30.0},
                        "segment": {"top_values": [{"value": "A", "percentage": 80.0}]},
                    },
                }
            ],
            "n_clusters": 1,
            "total_customers": 20,
        }
        text = self.generator._format_cluster_insights(cluster_result)
        assert "Cluster 0" in text
        assert "10 customers" in text
        assert "50.0%" in text

    def test_extract_persona_insights(self):
        result = {
            "personas": [
                {"title": "The Decision Maker"},
                {"title": "The Technical Evaluator"},
            ],
            "persona_comparison": {
                "coverage_gaps": ["SMB segment"],
            },
        }
        insights = PersonaGenerator._extract_persona_insights(result)
        assert len(insights) >= 1
        generated = [i for i in insights if i["type"] == "personas_generated"]
        assert generated[0]["count"] == 2
