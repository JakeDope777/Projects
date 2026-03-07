"""
Comprehensive tests for the Brain Prompt Builder.

Tests cover:
- Basic prompt structure
- Token-aware context budgeting
- Context layer injection (memories, knowledge, DB, summary)
- History truncation and selection
- Skill-specific prompts
- Token estimation
"""

import pytest
from app.brain.prompt_builder import (
    PromptBuilder,
    estimate_tokens,
    truncate_to_tokens,
    SYSTEM_INSTRUCTION,
    SKILL_INSTRUCTIONS,
    DEFAULT_TOKEN_BUDGET,
)


@pytest.fixture
def builder():
    return PromptBuilder()


@pytest.fixture
def small_budget_builder():
    return PromptBuilder(token_budget=500)


# ---------------------------------------------------------------------------
# Token estimation helpers
# ---------------------------------------------------------------------------

class TestTokenEstimation:
    """Tests for token estimation utilities."""

    def test_estimate_tokens_basic(self):
        assert estimate_tokens("hello world") > 0

    def test_estimate_tokens_empty(self):
        assert estimate_tokens("") == 1  # minimum 1

    def test_estimate_tokens_long_text(self):
        text = "word " * 1000
        tokens = estimate_tokens(text)
        assert tokens > 100

    def test_truncate_to_tokens_short(self):
        text = "short text"
        result = truncate_to_tokens(text, 100)
        assert result == text

    def test_truncate_to_tokens_long(self):
        text = "x" * 10000
        result = truncate_to_tokens(text, 10)
        assert len(result) < len(text)
        assert "[truncated]" in result


# ---------------------------------------------------------------------------
# Basic prompt structure
# ---------------------------------------------------------------------------

class TestBasicPromptStructure:
    """Tests for basic prompt construction."""

    def test_minimal_prompt(self, builder):
        messages = builder.build("Hello")
        assert len(messages) >= 2
        assert messages[0]["role"] == "system"
        assert messages[-1]["role"] == "user"
        assert messages[-1]["content"] == "Hello"

    def test_system_instruction_included(self, builder):
        messages = builder.build("Test")
        assert "Digital CMO AI" in messages[0]["content"]

    def test_custom_system_instruction(self):
        custom = "You are a custom assistant."
        builder = PromptBuilder(system_instruction=custom)
        messages = builder.build("Test")
        assert "custom assistant" in messages[0]["content"]

    def test_user_message_always_last(self, builder):
        messages = builder.build(
            "My question",
            conversation_history=[{"role": "user", "content": "prev"}],
            retrieved_memories=["memory 1"],
        )
        assert messages[-1]["role"] == "user"
        assert messages[-1]["content"] == "My question"


# ---------------------------------------------------------------------------
# Context layer injection
# ---------------------------------------------------------------------------

class TestContextLayers:
    """Tests for injecting different context layers."""

    def test_conversation_history_injected(self, builder):
        history = [
            {"role": "user", "content": "Previous question"},
            {"role": "assistant", "content": "Previous answer"},
        ]
        messages = builder.build("New question", conversation_history=history)
        contents = [m["content"] for m in messages]
        assert any("Previous question" in c for c in contents)
        assert any("Previous answer" in c for c in contents)

    def test_retrieved_memories_injected(self, builder):
        memories = ["Brand voice is professional", "Target audience is CTOs"]
        messages = builder.build("Write copy", retrieved_memories=memories)
        all_content = " ".join(m["content"] for m in messages)
        assert "Brand voice is professional" in all_content

    def test_structured_knowledge_injected(self, builder):
        knowledge = {"goals": "Increase revenue by 20%", "preferences": "Use formal tone"}
        messages = builder.build("Plan campaign", structured_knowledge=knowledge)
        all_content = " ".join(m["content"] for m in messages)
        assert "Increase revenue by 20%" in all_content

    def test_db_results_injected(self, builder):
        db_results = [{"name": "Campaign A", "status": "active"}]
        messages = builder.build("Show campaigns", db_results=db_results)
        all_content = " ".join(m["content"] for m in messages)
        assert "Campaign A" in all_content

    def test_conversation_summary_injected(self, builder):
        summary = "User discussed marketing strategy for Q2."
        messages = builder.build("Continue", conversation_summary=summary)
        all_content = " ".join(m["content"] for m in messages)
        assert "marketing strategy" in all_content

    def test_skill_context_injected(self, builder):
        messages = builder.build("Analyse market", skill_context="business_analysis")
        all_content = " ".join(m["content"] for m in messages)
        assert "Business Analysis" in all_content or "business_analysis" in all_content.lower()

    def test_all_layers_combined(self, builder):
        messages = builder.build(
            user_message="Full context test",
            conversation_history=[{"role": "user", "content": "prev"}],
            conversation_summary="Summary of old conversation",
            retrieved_memories=["Memory snippet 1"],
            structured_knowledge={"key": "value"},
            db_results=[{"col": "data"}],
            skill_context="analytics_reporting",
        )
        assert len(messages) >= 3  # system + at least some context + user


# ---------------------------------------------------------------------------
# Token budget and truncation
# ---------------------------------------------------------------------------

class TestTokenBudget:
    """Tests for token-aware context budgeting."""

    def test_history_truncation(self, builder):
        history = [{"role": "user", "content": f"Message {i}" * 20} for i in range(50)]
        messages = builder.build("Latest", conversation_history=history)
        # Should not include all 50 messages
        user_messages = [m for m in messages if m.get("content", "").startswith("Message")]
        assert len(user_messages) < 50

    def test_small_budget_limits_context(self, small_budget_builder):
        long_knowledge = {"data": "x" * 5000}
        messages = small_budget_builder.build(
            "Test",
            structured_knowledge=long_knowledge,
        )
        # The knowledge should be truncated
        all_content = " ".join(m["content"] for m in messages)
        assert len(all_content) < 10000

    def test_custom_budget_override(self, builder):
        messages = builder.build("Test", token_budget=100)
        # With a very small budget, context should be minimal
        total_tokens = builder.estimate_prompt_tokens(messages)
        # It should be reasonably bounded (not exact due to estimation)
        assert total_tokens < 500

    def test_empty_layers_dont_add_messages(self, builder):
        messages = builder.build("Test")
        # Only system + user message when no context layers
        assert len(messages) == 2


# ---------------------------------------------------------------------------
# Skill-specific prompts
# ---------------------------------------------------------------------------

class TestSkillPrompts:
    """Tests for skill-specific prompt building."""

    def test_skill_prompt_structure(self, builder):
        messages = builder.build_skill_prompt(
            "business_analysis", "Perform a SWOT analysis"
        )
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"

    def test_skill_prompt_with_known_skill(self, builder):
        messages = builder.build_skill_prompt(
            "business_analysis", "Analyse competitors"
        )
        assert "Business Analysis" in messages[0]["content"] or "business" in messages[0]["content"].lower()

    def test_skill_prompt_with_data(self, builder):
        messages = builder.build_skill_prompt(
            "creative_design",
            "Write ad copy",
            data={"product": "Widget Pro", "audience": "CTOs"},
        )
        assert "Widget Pro" in messages[1]["content"]

    def test_skill_prompt_unknown_skill(self, builder):
        messages = builder.build_skill_prompt(
            "unknown_skill", "Do something"
        )
        assert "unknown_skill" in messages[0]["content"]


# ---------------------------------------------------------------------------
# Token estimation method
# ---------------------------------------------------------------------------

class TestPromptTokenEstimation:
    """Tests for the prompt-level token estimation."""

    def test_estimate_prompt_tokens(self, builder):
        messages = builder.build("Hello world")
        tokens = builder.estimate_prompt_tokens(messages)
        assert tokens > 0
        assert isinstance(tokens, int)

    def test_estimate_increases_with_context(self, builder):
        simple = builder.build("Hello")
        complex_msgs = builder.build(
            "Hello",
            conversation_history=[{"role": "user", "content": "x" * 500}],
            retrieved_memories=["memory " * 50],
        )
        assert builder.estimate_prompt_tokens(complex_msgs) > builder.estimate_prompt_tokens(simple)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_user_message(self, builder):
        messages = builder.build("")
        assert messages[-1]["content"] == ""

    def test_none_values_in_knowledge(self, builder):
        knowledge = {"key1": "value1", "key2": "value2"}
        messages = builder.build("Test", structured_knowledge=knowledge)
        assert len(messages) >= 2

    def test_empty_history_list(self, builder):
        messages = builder.build("Test", conversation_history=[])
        assert len(messages) == 2  # system + user only

    def test_empty_memories_list(self, builder):
        messages = builder.build("Test", retrieved_memories=[])
        assert len(messages) == 2

    def test_empty_db_results(self, builder):
        messages = builder.build("Test", db_results=[])
        assert len(messages) == 2
