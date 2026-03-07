"""
Conversation Summarizer - compresses old conversation context into concise summaries.

Provides two summarisation strategies:
1. **Extractive** (rule-based) – selects the most important sentences from the
   conversation using keyword scoring and position heuristics.  Fast, no API call.
2. **Abstractive** (LLM-based) – generates a fluent summary via the configured
   LLM.  Higher quality but requires an API call.

The summariser is designed to be called periodically (e.g. every N turns) by the
orchestrator to keep the context window manageable.
"""

from __future__ import annotations

import re
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Importance keywords for extractive summarisation
# ---------------------------------------------------------------------------

_SUMMARY_KEYWORDS = {
    "decide", "decision", "goal", "target", "budget", "deadline",
    "strategy", "prefer", "preference", "important", "critical",
    "brand", "guideline", "always", "never", "remember", "key",
    "result", "metric", "kpi", "revenue", "cost", "plan",
    "launch", "campaign", "audience", "segment", "competitor",
    "action", "next step", "conclusion", "summary", "agreed",
}


# ---------------------------------------------------------------------------
# ConversationSummarizer
# ---------------------------------------------------------------------------

class ConversationSummarizer:
    """
    Compresses conversation history into a concise summary.

    Usage::

        summarizer = ConversationSummarizer()
        summary = summarizer.summarize(messages)
        # or with LLM:
        summary = await summarizer.summarize_with_llm(messages)
    """

    def __init__(
        self,
        max_summary_sentences: int = 10,
        llm_client: Optional[Any] = None,
    ):
        self.max_summary_sentences = max_summary_sentences
        self.llm_client = llm_client

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def summarize(
        self,
        messages: list[dict],
        existing_summary: Optional[str] = None,
    ) -> str:
        """
        Produce an extractive summary of the conversation.

        If an *existing_summary* is provided, the new summary is appended
        (rolling summary pattern).

        Args:
            messages: List of ``{"role": ..., "content": ...}`` dicts.
            existing_summary: Previous summary to build upon.

        Returns:
            A concise text summary.
        """
        if not messages:
            return existing_summary or ""

        # Score and rank sentences across all messages
        scored_sentences = self._score_all_sentences(messages)

        # Select top sentences
        top = scored_sentences[: self.max_summary_sentences]
        summary_lines = [sent for _, sent in top]

        new_summary = " ".join(summary_lines)

        if existing_summary:
            # Merge: keep the existing summary and append new highlights
            combined = f"{existing_summary}\n\nUpdate: {new_summary}"
            # Trim if too long
            if len(combined) > 3000:
                combined = combined[:3000] + "..."
            return combined

        return new_summary

    async def summarize_with_llm(
        self,
        messages: list[dict],
        existing_summary: Optional[str] = None,
    ) -> str:
        """
        Produce an abstractive summary using the LLM.
        Falls back to extractive summarisation if the LLM is unavailable.
        """
        if self.llm_client is None:
            return self.summarize(messages, existing_summary)

        try:
            conversation_text = self._format_conversation(messages)

            prompt_parts = [
                "Summarise the following conversation concisely. Focus on:",
                "- Key decisions made",
                "- Goals and targets discussed",
                "- Important facts and data points",
                "- Action items and next steps",
                "- User preferences and instructions",
                "",
                "Keep the summary under 200 words. Use bullet points.",
                "",
            ]

            if existing_summary:
                prompt_parts.extend([
                    "Previous summary:",
                    existing_summary,
                    "",
                    "New conversation to incorporate:",
                ])

            prompt_parts.extend([
                "Conversation:",
                conversation_text,
                "",
                "Summary:",
            ])

            prompt = "\n".join(prompt_parts)
            response = await self.llm_client.generate(prompt)
            return response.strip()
        except Exception:
            return self.summarize(messages, existing_summary)

    def should_summarize(
        self,
        message_count: int,
        threshold: int = 20,
    ) -> bool:
        """
        Determine whether the conversation should be summarised based on
        the number of messages.

        Args:
            message_count: Current number of messages in the conversation.
            threshold: Summarise when message count exceeds this value.

        Returns:
            True if summarisation is recommended.
        """
        return message_count >= threshold

    def split_conversation(
        self,
        messages: list[dict],
        keep_recent: int = 10,
    ) -> tuple[list[dict], list[dict]]:
        """
        Split a conversation into older messages (to summarise) and recent
        messages (to keep verbatim).

        Args:
            messages: Full conversation history.
            keep_recent: Number of recent messages to preserve.

        Returns:
            Tuple of ``(older_messages, recent_messages)``.
        """
        if len(messages) <= keep_recent:
            return [], messages
        split_point = len(messages) - keep_recent
        return messages[:split_point], messages[split_point:]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _score_all_sentences(
        self, messages: list[dict]
    ) -> list[tuple[float, str]]:
        """Score all sentences across all messages and return sorted list."""
        all_scored: list[tuple[float, str]] = []
        total_messages = len(messages)

        for i, msg in enumerate(messages):
            content = msg.get("content", "")
            role = msg.get("role", "user")
            sentences = self._split_sentences(content)

            for j, sent in enumerate(sentences):
                if len(sent.strip()) < 10:
                    continue
                score = self._score_sentence(sent)

                # Position bonus: later messages are more relevant
                position_bonus = (i / max(total_messages, 1)) * 0.2
                score += position_bonus

                # Role bonus: user messages often contain key info
                if role == "user":
                    score += 0.1

                # First/last sentence bonus
                if j == 0 or j == len(sentences) - 1:
                    score += 0.05

                all_scored.append((score, sent.strip()))

        all_scored.sort(key=lambda x: x[0], reverse=True)
        return all_scored

    def _score_sentence(self, sentence: str) -> float:
        """Score a single sentence based on keyword presence."""
        words = set(re.findall(r"[a-z]+", sentence.lower()))
        hits = words & _SUMMARY_KEYWORDS
        score = len(hits) * 0.15

        # Bonus for sentences with numbers (often contain data)
        if re.search(r"\d+", sentence):
            score += 0.1

        # Bonus for sentences with specific markers
        if re.search(r"\b(we|our|I)\b", sentence, re.IGNORECASE):
            score += 0.05

        return score

    @staticmethod
    def _split_sentences(text: str) -> list[str]:
        """Split text into sentences."""
        return re.split(r"(?<=[.!?])\s+", text)

    @staticmethod
    def _format_conversation(messages: list[dict]) -> str:
        """Format messages into a readable conversation transcript."""
        lines = []
        for msg in messages:
            role = msg.get("role", "unknown").capitalize()
            content = msg.get("content", "")
            lines.append(f"{role}: {content}")
        return "\n".join(lines)
