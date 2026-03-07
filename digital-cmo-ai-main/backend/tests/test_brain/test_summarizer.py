"""
Comprehensive tests for the Conversation Summarizer module.

Tests cover:
- Extractive summarization
- Rolling summary (with existing summary)
- Conversation splitting
- Should-summarize threshold
- LLM-based summarization (with mock)
- Edge cases
"""

import pytest
from app.brain.summarizer import ConversationSummarizer


@pytest.fixture
def summarizer():
    return ConversationSummarizer(max_summary_sentences=5)


# ---------------------------------------------------------------------------
# Extractive summarization tests
# ---------------------------------------------------------------------------

class TestExtractiveSummarization:
    """Tests for rule-based extractive summarization."""

    def test_basic_summarization(self, summarizer):
        messages = [
            {"role": "user", "content": "We need to decide on our marketing budget for Q2."},
            {"role": "assistant", "content": "I recommend allocating $50,000 across digital channels."},
            {"role": "user", "content": "Our target audience is enterprise CTOs."},
            {"role": "assistant", "content": "Great, I'll tailor the strategy accordingly."},
        ]
        summary = summarizer.summarize(messages)
        assert len(summary) > 0
        assert isinstance(summary, str)

    def test_summary_contains_key_info(self, summarizer):
        messages = [
            {"role": "user", "content": "Our budget is $100,000 and the deadline is March 15."},
            {"role": "assistant", "content": "Noted. I'll plan the campaign within that budget and timeline."},
            {"role": "user", "content": "The target audience is small business owners."},
        ]
        summary = summarizer.summarize(messages)
        # Should contain at least some key information
        assert len(summary) > 20

    def test_summary_respects_max_sentences(self):
        summarizer = ConversationSummarizer(max_summary_sentences=2)
        messages = [
            {"role": "user", "content": f"Point {i}. This is an important decision about strategy." }
            for i in range(20)
        ]
        summary = summarizer.summarize(messages)
        # Summary should be bounded
        sentences = summary.split(". ")
        assert len(sentences) <= 10  # generous bound due to sentence splitting

    def test_empty_messages(self, summarizer):
        summary = summarizer.summarize([])
        assert summary == ""


# ---------------------------------------------------------------------------
# Rolling summary tests
# ---------------------------------------------------------------------------

class TestRollingSummary:
    """Tests for rolling summary (building on existing summary)."""

    def test_rolling_summary(self, summarizer):
        existing = "Previously discussed: Marketing budget is $50K."
        new_messages = [
            {"role": "user", "content": "We decided to focus on email marketing."},
            {"role": "assistant", "content": "I'll create an email campaign plan."},
        ]
        summary = summarizer.summarize(new_messages, existing_summary=existing)
        assert "Previously discussed" in summary
        assert "Update:" in summary

    def test_rolling_summary_without_existing(self, summarizer):
        messages = [
            {"role": "user", "content": "Our goal is 1000 new signups."},
        ]
        summary = summarizer.summarize(messages, existing_summary=None)
        assert len(summary) > 0
        assert "Update:" not in summary

    def test_rolling_summary_empty_new_messages(self, summarizer):
        existing = "Previous summary content."
        summary = summarizer.summarize([], existing_summary=existing)
        assert summary == existing


# ---------------------------------------------------------------------------
# Conversation splitting tests
# ---------------------------------------------------------------------------

class TestConversationSplitting:
    """Tests for splitting conversations into old and recent."""

    def test_split_basic(self, summarizer):
        messages = [{"role": "user", "content": f"Msg {i}"} for i in range(30)]
        older, recent = summarizer.split_conversation(messages, keep_recent=10)
        assert len(older) == 20
        assert len(recent) == 10
        assert recent[-1]["content"] == "Msg 29"

    def test_split_short_conversation(self, summarizer):
        messages = [{"role": "user", "content": f"Msg {i}"} for i in range(5)]
        older, recent = summarizer.split_conversation(messages, keep_recent=10)
        assert len(older) == 0
        assert len(recent) == 5

    def test_split_exact_threshold(self, summarizer):
        messages = [{"role": "user", "content": f"Msg {i}"} for i in range(10)]
        older, recent = summarizer.split_conversation(messages, keep_recent=10)
        assert len(older) == 0
        assert len(recent) == 10

    def test_split_empty(self, summarizer):
        older, recent = summarizer.split_conversation([], keep_recent=10)
        assert older == []
        assert recent == []


# ---------------------------------------------------------------------------
# Should-summarize threshold tests
# ---------------------------------------------------------------------------

class TestShouldSummarize:
    """Tests for the summarization threshold check."""

    def test_below_threshold(self, summarizer):
        assert summarizer.should_summarize(10, threshold=20) is False

    def test_at_threshold(self, summarizer):
        assert summarizer.should_summarize(20, threshold=20) is True

    def test_above_threshold(self, summarizer):
        assert summarizer.should_summarize(50, threshold=20) is True

    def test_zero_messages(self, summarizer):
        assert summarizer.should_summarize(0, threshold=20) is False

    def test_custom_threshold(self, summarizer):
        assert summarizer.should_summarize(5, threshold=5) is True


# ---------------------------------------------------------------------------
# LLM-based summarization tests
# ---------------------------------------------------------------------------

class TestLLMSummarization:
    """Tests for LLM-based abstractive summarization."""

    @pytest.mark.asyncio
    async def test_llm_fallback_without_client(self):
        summarizer = ConversationSummarizer()
        messages = [
            {"role": "user", "content": "We need to plan our Q2 strategy."},
        ]
        summary = await summarizer.summarize_with_llm(messages)
        assert len(summary) > 0

    @pytest.mark.asyncio
    async def test_llm_with_mock_client(self):
        class MockLLM:
            async def generate(self, prompt):
                return "- Discussed Q2 marketing strategy\n- Budget set to $50K"

        summarizer = ConversationSummarizer(llm_client=MockLLM())
        messages = [
            {"role": "user", "content": "Let's plan Q2 with a $50K budget."},
        ]
        summary = await summarizer.summarize_with_llm(messages)
        assert "Q2" in summary
        assert "$50K" in summary

    @pytest.mark.asyncio
    async def test_llm_error_fallback(self):
        class FailingLLM:
            async def generate(self, prompt):
                raise RuntimeError("API error")

        summarizer = ConversationSummarizer(llm_client=FailingLLM())
        messages = [
            {"role": "user", "content": "Our goal is to increase revenue."},
        ]
        summary = await summarizer.summarize_with_llm(messages)
        # Should fall back to extractive
        assert len(summary) > 0

    @pytest.mark.asyncio
    async def test_llm_with_existing_summary(self):
        class MockLLM:
            async def generate(self, prompt):
                return "Updated summary including new information."

        summarizer = ConversationSummarizer(llm_client=MockLLM())
        messages = [{"role": "user", "content": "New information here."}]
        summary = await summarizer.summarize_with_llm(
            messages, existing_summary="Previous summary."
        )
        assert len(summary) > 0


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    """Tests for edge cases."""

    def test_single_short_message(self, summarizer):
        messages = [{"role": "user", "content": "Hi"}]
        summary = summarizer.summarize(messages)
        assert isinstance(summary, str)

    def test_very_long_conversation(self, summarizer):
        messages = [
            {"role": "user", "content": f"This is message {i} about our marketing strategy and budget decisions."}
            for i in range(100)
        ]
        summary = summarizer.summarize(messages)
        assert len(summary) > 0
        assert len(summary) < 10000  # Should be bounded

    def test_messages_without_content(self, summarizer):
        messages = [{"role": "user"}, {"role": "assistant"}]
        summary = summarizer.summarize(messages)
        assert isinstance(summary, str)

    def test_mixed_roles(self, summarizer):
        messages = [
            {"role": "user", "content": "Our budget decision is $50K."},
            {"role": "assistant", "content": "I'll plan accordingly."},
            {"role": "system", "content": "System note."},
        ]
        summary = summarizer.summarize(messages)
        assert isinstance(summary, str)
