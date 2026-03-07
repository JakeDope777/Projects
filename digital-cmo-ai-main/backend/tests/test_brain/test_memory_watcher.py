"""
Comprehensive tests for the Memory Watcher module.

Tests cover:
- Fact extraction from conversations
- Importance scoring
- Different fact types (decisions, preferences, goals, etc.)
- LLM-based extraction (with mock)
- Edge cases
"""

import pytest
from app.brain.memory_watcher import MemoryWatcher


@pytest.fixture
def watcher():
    return MemoryWatcher(importance_threshold=0.3)


@pytest.fixture
def sensitive_watcher():
    """Watcher with a low threshold to catch more facts."""
    return MemoryWatcher(importance_threshold=0.1)


# ---------------------------------------------------------------------------
# Basic extraction tests
# ---------------------------------------------------------------------------

class TestBasicExtraction:
    """Tests for rule-based fact extraction."""

    def test_extract_decision(self, watcher):
        messages = [
            {"role": "user", "content": "We decided to use email marketing as our primary channel."},
        ]
        facts = watcher.extract_facts(messages)
        assert len(facts) >= 1
        assert any("decision" in f["metadata"]["type"] for f in facts)

    def test_extract_preference(self, watcher):
        messages = [
            {"role": "user", "content": "I prefer a formal tone in all communications."},
        ]
        facts = watcher.extract_facts(messages)
        assert len(facts) >= 1
        assert any("preference" in f["metadata"]["type"] for f in facts)

    def test_extract_goal(self, watcher):
        messages = [
            {"role": "user", "content": "Our goal is to increase conversion rate by 25%."},
        ]
        facts = watcher.extract_facts(messages)
        assert len(facts) >= 1
        assert any("goal" in f["metadata"]["type"] for f in facts)

    def test_extract_brand_guideline(self, watcher):
        messages = [
            {"role": "user", "content": "Our brand voice should always be friendly and approachable."},
        ]
        facts = watcher.extract_facts(messages)
        assert len(facts) >= 1

    def test_extract_instruction(self, watcher):
        messages = [
            {"role": "user", "content": "Always include a call-to-action in every email."},
        ]
        facts = watcher.extract_facts(messages)
        assert len(facts) >= 1
        assert any("instruction" in f["metadata"]["type"] for f in facts)

    def test_extract_fact_with_numbers(self, sensitive_watcher):
        messages = [
            {"role": "user", "content": "Our budget is $50,000 for Q2 marketing."},
        ]
        facts = sensitive_watcher.extract_facts(messages)
        assert len(facts) >= 1

    def test_no_extraction_for_trivial(self, watcher):
        messages = [
            {"role": "user", "content": "Hello"},
        ]
        facts = watcher.extract_facts(messages)
        assert len(facts) == 0

    def test_no_extraction_for_short_messages(self, watcher):
        messages = [
            {"role": "user", "content": "OK"},
        ]
        facts = watcher.extract_facts(messages)
        assert len(facts) == 0


# ---------------------------------------------------------------------------
# Metadata tests
# ---------------------------------------------------------------------------

class TestMetadata:
    """Tests for metadata attached to extracted facts."""

    def test_metadata_has_type(self, watcher):
        messages = [
            {"role": "user", "content": "We decided to launch in March."},
        ]
        facts = watcher.extract_facts(messages)
        assert all("type" in f["metadata"] for f in facts)

    def test_metadata_has_timestamp(self, watcher):
        messages = [
            {"role": "user", "content": "Our goal is 1000 signups."},
        ]
        facts = watcher.extract_facts(messages)
        assert all("timestamp" in f["metadata"] for f in facts)

    def test_metadata_has_role(self, watcher):
        messages = [
            {"role": "assistant", "content": "I've noted your decision to focus on email marketing."},
        ]
        facts = watcher.extract_facts(messages)
        if facts:
            assert all(f["metadata"]["role"] == "assistant" for f in facts)

    def test_metadata_includes_conversation_id(self, watcher):
        messages = [
            {"role": "user", "content": "We decided to use React for the frontend."},
        ]
        facts = watcher.extract_facts(messages, conversation_id="conv-123")
        if facts:
            assert all(f["metadata"]["conversation_id"] == "conv-123" for f in facts)

    def test_metadata_includes_user_id(self, watcher):
        messages = [
            {"role": "user", "content": "Our strategy is to target enterprise customers."},
        ]
        facts = watcher.extract_facts(messages, user_id="user-456")
        if facts:
            assert all(f["metadata"]["user_id"] == "user-456" for f in facts)

    def test_metadata_has_importance_score(self, watcher):
        messages = [
            {"role": "user", "content": "We decided to increase the budget to $100,000."},
        ]
        facts = watcher.extract_facts(messages)
        assert all("importance" in f["metadata"] for f in facts)
        assert all(isinstance(f["metadata"]["importance"], float) for f in facts)


# ---------------------------------------------------------------------------
# Importance scoring tests
# ---------------------------------------------------------------------------

class TestImportanceScoring:
    """Tests for the importance scoring mechanism."""

    def test_high_importance_decision(self, watcher):
        score = watcher.score_importance(
            "We decided to allocate our entire budget to digital marketing."
        )
        assert score >= 0.3

    def test_low_importance_greeting(self, watcher):
        score = watcher.score_importance("Hello, how are you?")
        assert score < 0.3

    def test_importance_increases_with_keywords(self, watcher):
        low = watcher.score_importance("The sky is blue.")
        high = watcher.score_importance(
            "This is an important and critical decision about our strategy and budget."
        )
        assert high > low

    def test_importance_capped_at_one(self, watcher):
        score = watcher.score_importance(
            "We decided our important critical goal strategy budget deadline "
            "brand guideline preference always never remember must required."
        )
        assert score <= 1.0


# ---------------------------------------------------------------------------
# Multiple messages tests
# ---------------------------------------------------------------------------

class TestMultipleMessages:
    """Tests for extracting from multiple messages at once."""

    def test_multiple_messages(self, watcher):
        messages = [
            {"role": "user", "content": "We decided to use HubSpot for CRM."},
            {"role": "assistant", "content": "Great choice! I'll remember that."},
            {"role": "user", "content": "Our goal is 500 new leads per month."},
            {"role": "user", "content": "What's the weather like?"},
        ]
        facts = watcher.extract_facts(messages)
        # Should extract at least the decision and goal
        assert len(facts) >= 2

    def test_assistant_messages_also_extracted(self, sensitive_watcher):
        messages = [
            {"role": "assistant", "content": "Based on your preference, I'll always use a formal tone."},
        ]
        facts = sensitive_watcher.extract_facts(messages)
        # Assistant messages with key info should also be extracted
        assert len(facts) >= 1


# ---------------------------------------------------------------------------
# LLM-based extraction tests
# ---------------------------------------------------------------------------

class TestLLMExtraction:
    """Tests for LLM-based fact extraction."""

    @pytest.mark.asyncio
    async def test_llm_extraction_fallback(self):
        watcher = MemoryWatcher()
        messages = [
            {"role": "user", "content": "We decided to launch in Q2."},
        ]
        facts = await watcher.extract_facts_with_llm(messages)
        # Should fall back to rule-based extraction
        assert len(facts) >= 1

    @pytest.mark.asyncio
    async def test_llm_extraction_with_mock(self):
        class MockLLM:
            async def generate(self, prompt):
                return (
                    "decision: Launch product in Q2 2025\n"
                    "goal: Achieve 1000 signups in first month\n"
                    "preference: Use formal communication tone\n"
                )

        watcher = MemoryWatcher(llm_client=MockLLM())
        messages = [{"role": "user", "content": "dummy"}]
        facts = await watcher.extract_facts_with_llm(messages)
        assert len(facts) == 3
        types = {f["metadata"]["type"] for f in facts}
        assert "decision" in types
        assert "goal" in types
        assert "preference" in types

    @pytest.mark.asyncio
    async def test_llm_extraction_error_fallback(self):
        class FailingLLM:
            async def generate(self, prompt):
                raise RuntimeError("API error")

        watcher = MemoryWatcher(llm_client=FailingLLM())
        messages = [
            {"role": "user", "content": "We decided to use email marketing."},
        ]
        facts = await watcher.extract_facts_with_llm(messages)
        # Should fall back to rule-based
        assert len(facts) >= 1


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_messages(self, watcher):
        facts = watcher.extract_facts([])
        assert facts == []

    def test_empty_content(self, watcher):
        messages = [{"role": "user", "content": ""}]
        facts = watcher.extract_facts(messages)
        assert facts == []

    def test_missing_content_key(self, watcher):
        messages = [{"role": "user"}]
        facts = watcher.extract_facts(messages)
        assert facts == []

    def test_very_long_message(self, sensitive_watcher):
        long_msg = "Our strategy is to " + "expand into new markets. " * 100
        messages = [{"role": "user", "content": long_msg}]
        facts = sensitive_watcher.extract_facts(messages)
        # Should still extract without error
        assert isinstance(facts, list)
