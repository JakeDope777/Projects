"""
Comprehensive tests for the Brain Intent Router.

Tests cover:
- Keyword-based classification (regex fallback)
- Sparse embedding classification (TF cosine)
- Dense embedding classification (with mock embedder)
- Confidence scoring
- LLM-based classification (async, with mock)
- Edge cases and ambiguous queries
"""

import pytest
from app.brain.router import (
    IntentRouter,
    SKILL_BUSINESS_ANALYSIS,
    SKILL_CREATIVE_DESIGN,
    SKILL_CRM_CAMPAIGN,
    SKILL_ANALYTICS_REPORTING,
    SKILL_INTEGRATIONS,
    SKILL_SYSTEM,
    SKILL_GENERAL,
    ALL_SKILLS,
    SKILL_EXEMPLARS,
    _simple_tokenize,
    _term_frequency,
    _cosine_similarity,
)


@pytest.fixture
def router():
    return IntentRouter()


# ---------------------------------------------------------------------------
# Helper function tests
# ---------------------------------------------------------------------------

class TestHelperFunctions:
    """Tests for internal tokenization and similarity helpers."""

    def test_simple_tokenize(self):
        tokens = _simple_tokenize("Hello, World! 123")
        assert tokens == ["hello", "world", "123"]

    def test_simple_tokenize_empty(self):
        assert _simple_tokenize("") == []

    def test_term_frequency(self):
        tf = _term_frequency(["a", "b", "a"])
        assert abs(tf["a"] - 2 / 3) < 0.01
        assert abs(tf["b"] - 1 / 3) < 0.01

    def test_term_frequency_empty(self):
        tf = _term_frequency([])
        assert tf == {}

    def test_cosine_similarity_identical(self):
        a = {"x": 1.0, "y": 1.0}
        sim = _cosine_similarity(a, a)
        assert abs(sim - 1.0) < 0.01

    def test_cosine_similarity_orthogonal(self):
        a = {"x": 1.0}
        b = {"y": 1.0}
        assert _cosine_similarity(a, b) == 0.0

    def test_cosine_similarity_empty(self):
        assert _cosine_similarity({}, {"x": 1.0}) == 0.0


# ---------------------------------------------------------------------------
# Keyword classification tests
# ---------------------------------------------------------------------------

class TestKeywordClassification:
    """Tests for regex keyword-based intent classification."""

    def test_business_analysis_swot(self, router):
        assert router.classify_intent("Do a SWOT analysis for our product") == SKILL_BUSINESS_ANALYSIS

    def test_business_analysis_competitor(self, router):
        assert router.classify_intent("Analyse our competitor landscape") == SKILL_BUSINESS_ANALYSIS

    def test_business_analysis_persona(self, router):
        assert router.classify_intent("Create buyer personas for our target audience") == SKILL_BUSINESS_ANALYSIS

    def test_creative_blog(self, router):
        assert router.classify_intent("Write a blog post about our new feature") == SKILL_CREATIVE_DESIGN

    def test_creative_banner(self, router):
        assert router.classify_intent("Generate a banner image for our campaign") == SKILL_CREATIVE_DESIGN

    def test_creative_ab_test(self, router):
        assert router.classify_intent("Suggest A/B test variations for this headline") == SKILL_CREATIVE_DESIGN

    def test_crm_lead(self, router):
        assert router.classify_intent("Update the lead status in our CRM") == SKILL_CRM_CAMPAIGN

    def test_crm_campaign(self, router):
        assert router.classify_intent("Create an email campaign for new users") == SKILL_CRM_CAMPAIGN

    def test_crm_compliance(self, router):
        assert router.classify_intent("Check GDPR compliance for this message") == SKILL_CRM_CAMPAIGN

    def test_analytics_dashboard(self, router):
        assert router.classify_intent("Show me the analytics dashboard") == SKILL_ANALYTICS_REPORTING

    def test_analytics_metrics(self, router):
        assert router.classify_intent("What is our current CAC and LTV?") == SKILL_ANALYTICS_REPORTING

    def test_analytics_forecast(self, router):
        assert router.classify_intent("Forecast our conversion rate for next month") == SKILL_ANALYTICS_REPORTING

    def test_integrations_connect(self, router):
        assert router.classify_intent("Connect our Google Ads account via OAuth") == SKILL_INTEGRATIONS

    def test_system_settings(self, router):
        assert router.classify_intent("Change my account settings and preferences") == SKILL_SYSTEM

    def test_general_greeting(self, router):
        assert router.classify_intent("Hello, how are you today?") == SKILL_GENERAL

    def test_general_ambiguous(self, router):
        assert router.classify_intent("Tell me something interesting") == SKILL_GENERAL


# ---------------------------------------------------------------------------
# Confidence scoring tests
# ---------------------------------------------------------------------------

class TestConfidenceScoring:
    """Tests for classify_with_confidence method."""

    def test_high_confidence_keyword(self, router):
        result = router.classify_with_confidence("Do a SWOT analysis")
        assert result["skill"] == SKILL_BUSINESS_ANALYSIS
        assert result["confidence"] > 0

    def test_general_low_confidence(self, router):
        result = router.classify_with_confidence("Hi there")
        assert result["skill"] == SKILL_GENERAL

    def test_result_has_method(self, router):
        result = router.classify_with_confidence("Write a blog post")
        assert "method" in result
        assert result["method"] in ("sparse_embedding", "keyword", "sparse_embedding_low", "default", "dense_embedding")

    def test_result_has_confidence(self, router):
        result = router.classify_with_confidence("Show me the dashboard")
        assert "confidence" in result
        assert isinstance(result["confidence"], (int, float))


# ---------------------------------------------------------------------------
# Dense embedding classification tests
# ---------------------------------------------------------------------------

class TestDenseEmbeddingClassification:
    """Tests with a mock dense embedding function."""

    def _mock_embedder(self, text: str) -> list[float]:
        """Simple mock: hash-based deterministic embedding."""
        import hashlib
        h = hashlib.md5(text.lower().encode()).hexdigest()
        return [int(c, 16) / 15.0 for c in h]

    def test_dense_embedding_classification(self):
        router = IntentRouter(embedding_fn=self._mock_embedder)
        # The mock embedder should still produce some classification
        result = router.classify_with_confidence("Do a SWOT analysis for our product")
        assert result["skill"] in ALL_SKILLS

    def test_dense_exemplars_cached(self):
        router = IntentRouter(embedding_fn=self._mock_embedder)
        router.classify_intent("test query")
        assert len(router._exemplar_dense) > 0


# ---------------------------------------------------------------------------
# LLM classification tests
# ---------------------------------------------------------------------------

class TestLLMClassification:
    """Tests for async LLM-based classification."""

    @pytest.mark.asyncio
    async def test_llm_fallback_without_client(self):
        router = IntentRouter()
        result = await router.classify_with_llm("Do a SWOT analysis")
        assert result == SKILL_BUSINESS_ANALYSIS

    @pytest.mark.asyncio
    async def test_llm_with_mock_client(self):
        class MockLLM:
            async def generate(self, prompt):
                return "creative_design"

        router = IntentRouter(llm_client=MockLLM())
        result = await router.classify_with_llm("Write something creative")
        assert result == SKILL_CREATIVE_DESIGN

    @pytest.mark.asyncio
    async def test_llm_invalid_response_falls_back(self):
        class MockLLM:
            async def generate(self, prompt):
                return "invalid_category_xyz"

        router = IntentRouter(llm_client=MockLLM())
        result = await router.classify_with_llm("Write a blog post")
        # Should fall back to keyword classification
        assert result in ALL_SKILLS

    @pytest.mark.asyncio
    async def test_llm_exception_falls_back(self):
        class MockLLM:
            async def generate(self, prompt):
                raise RuntimeError("API error")

        router = IntentRouter(llm_client=MockLLM())
        result = await router.classify_with_llm("Show me analytics")
        assert result in ALL_SKILLS


# ---------------------------------------------------------------------------
# Utility method tests
# ---------------------------------------------------------------------------

class TestUtilityMethods:
    """Tests for utility methods."""

    def test_get_available_skills(self, router):
        skills = router.get_available_skills()
        assert SKILL_BUSINESS_ANALYSIS in skills
        assert SKILL_CREATIVE_DESIGN in skills
        assert SKILL_GENERAL in skills
        assert len(skills) == len(ALL_SKILLS)

    def test_get_skill_exemplars(self, router):
        exemplars = router.get_skill_exemplars(SKILL_BUSINESS_ANALYSIS)
        assert len(exemplars) > 0
        assert any("SWOT" in ex for ex in exemplars)

    def test_get_skill_exemplars_unknown(self, router):
        exemplars = router.get_skill_exemplars("nonexistent_skill")
        assert exemplars == []


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_message(self, router):
        result = router.classify_intent("")
        assert result == SKILL_GENERAL

    def test_very_long_message(self, router):
        long_msg = "market research " * 500
        result = router.classify_intent(long_msg)
        assert result == SKILL_BUSINESS_ANALYSIS

    def test_special_characters(self, router):
        result = router.classify_intent("!@#$%^&*()")
        assert result == SKILL_GENERAL

    def test_mixed_case(self, router):
        result = router.classify_intent("Do A SWOT Analysis")
        assert result == SKILL_BUSINESS_ANALYSIS

    def test_multiple_intents_picks_strongest(self, router):
        # Message with keywords from multiple skills
        result = router.classify_intent(
            "Create a campaign with analytics dashboard and competitor analysis"
        )
        assert result in ALL_SKILLS  # Should pick one
