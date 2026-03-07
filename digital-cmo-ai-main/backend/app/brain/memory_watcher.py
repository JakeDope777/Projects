"""
Memory Watcher - automatically extracts and stores key facts from conversations.

The watcher analyses each new message pair (user + assistant) and identifies:
- **Decisions** – explicit choices or commitments.
- **Preferences** – stated likes, dislikes, or style requirements.
- **Facts** – concrete data points (budgets, dates, names, metrics).
- **Goals** – objectives or targets.
- **Brand guidelines** – tone, voice, visual identity rules.
- **Instructions** – standing orders ("always …", "never …").

Extracted facts are stored in the vector store with rich metadata so they can
be retrieved semantically later.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Extraction patterns (rule-based, fast)
# ---------------------------------------------------------------------------

# Each pattern maps to a fact *type* and a compiled regex.
_FACT_PATTERNS: list[tuple[str, re.Pattern]] = [
    # Decisions
    ("decision", re.compile(
        r"\b(we\s+decided|decision\s+is|let'?s\s+go\s+with|I\s+choose|"
        r"we(?:'re|\s+are)\s+going\s+(?:to|with)|final\s+choice)\b",
        re.IGNORECASE,
    )),
    # Preferences
    ("preference", re.compile(
        r"\b(I\s+prefer|we\s+prefer|I\s+like|I\s+don'?t\s+like|"
        r"please\s+(?:always|never)|our\s+preference|"
        r"I\s+want|we\s+want)\b",
        re.IGNORECASE,
    )),
    # Goals / targets
    ("goal", re.compile(
        r"\b(our\s+goal|target\s+is|objective|aim\s+(?:to|for)|"
        r"we\s+need\s+to|milestone|kpi\s+is|success\s+metric)\b",
        re.IGNORECASE,
    )),
    # Brand guidelines
    ("brand_guideline", re.compile(
        r"\b(brand\s+(?:voice|tone|guideline|identity|color|colour|font)|"
        r"style\s+guide|visual\s+identity|logo\s+usage|"
        r"tone\s+of\s+voice|brand\s+personality)\b",
        re.IGNORECASE,
    )),
    # Standing instructions
    ("instruction", re.compile(
        r"\b(always\s+(?:use|include|remember|mention)|"
        r"never\s+(?:use|include|mention|forget)|"
        r"make\s+sure\s+to|from\s+now\s+on|going\s+forward)\b",
        re.IGNORECASE,
    )),
    # Concrete facts (budgets, dates, metrics)
    ("fact", re.compile(
        r"\b(budget\s+is|deadline\s+is|launch\s+date|"
        r"(?:our|the)\s+(?:revenue|cac|ltv|arpu|mrr|arr)\s+is|"
        r"we\s+(?:have|had|spent)\s+\$[\d,]+|"
        r"(?:target|current)\s+(?:audience|market)\s+is)\b",
        re.IGNORECASE,
    )),
    # Numeric facts (catch monetary values, percentages, dates)
    ("fact", re.compile(
        r"(?:\$[\d,]+(?:\.\d{2})?|\d+%|\d{1,2}/\d{1,2}/\d{2,4})",
    )),
]

# Keywords that boost the importance of a message (even without pattern match)
_IMPORTANCE_KEYWORDS = {
    "important", "critical", "remember", "key", "essential",
    "priority", "urgent", "must", "required", "mandatory",
    "strategy", "budget", "deadline", "brand", "guideline",
}


# ---------------------------------------------------------------------------
# MemoryWatcher
# ---------------------------------------------------------------------------

class MemoryWatcher:
    """
    Watches conversation messages and extracts salient facts for long-term storage.

    Usage::

        watcher = MemoryWatcher()
        facts = watcher.extract_facts(messages)
        for fact in facts:
            vector_store.add(fact["text"], metadata=fact["metadata"])
    """

    def __init__(
        self,
        importance_threshold: float = 0.3,
        llm_client: Optional[Any] = None,
    ):
        """
        Args:
            importance_threshold: Minimum importance score (0-1) for a message
                to be considered worth extracting.
            llm_client: Optional async LLM client for advanced extraction.
        """
        self.importance_threshold = importance_threshold
        self.llm_client = llm_client

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract_facts(
        self,
        messages: list[dict],
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> list[dict]:
        """
        Analyse a list of messages and return extracted facts.

        Each fact is a dict with:
        - ``text``: the original message content.
        - ``metadata``: dict with ``type``, ``timestamp``, ``role``,
          ``conversation_id``, ``user_id``, ``importance``.

        Args:
            messages: List of ``{"role": ..., "content": ...}`` dicts.
            conversation_id: Optional conversation identifier.
            user_id: Optional user identifier.

        Returns:
            List of extracted fact dicts ready for vector store insertion.
        """
        facts: list[dict] = []
        now = datetime.now(timezone.utc).isoformat()

        for msg in messages:
            content = msg.get("content", "")
            role = msg.get("role", "unknown")

            if not content or len(content) < 10:
                continue

            # Score the message
            importance, fact_types = self._score_message(content)

            if importance >= self.importance_threshold:
                # Extract the most relevant sentences
                key_sentences = self._extract_key_sentences(content, fact_types)
                text_to_store = key_sentences if key_sentences else content

                metadata = {
                    "type": ",".join(sorted(fact_types)) if fact_types else "general",
                    "timestamp": now,
                    "role": role,
                    "importance": round(importance, 3),
                    "source": "memory_watcher",
                }
                if conversation_id:
                    metadata["conversation_id"] = conversation_id
                if user_id:
                    metadata["user_id"] = user_id

                facts.append({"text": text_to_store, "metadata": metadata})

        return facts

    async def extract_facts_with_llm(
        self,
        messages: list[dict],
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> list[dict]:
        """
        Use an LLM to extract structured facts from messages.
        Falls back to rule-based extraction if the LLM is unavailable.
        """
        if self.llm_client is None:
            return self.extract_facts(messages, conversation_id, user_id)

        try:
            content_block = "\n".join(
                f"[{m.get('role', '?')}]: {m.get('content', '')}" for m in messages
            )
            prompt = (
                "Extract key facts, decisions, preferences, goals, and instructions "
                "from the following conversation. Return each fact on a separate line "
                "with a type prefix.\n\n"
                "Format: TYPE: fact text\n"
                "Valid types: decision, preference, goal, brand_guideline, instruction, fact\n\n"
                f"Conversation:\n{content_block}\n\n"
                "Extracted facts:"
            )
            response = await self.llm_client.generate(prompt)
            return self._parse_llm_facts(response, conversation_id, user_id)
        except Exception:
            return self.extract_facts(messages, conversation_id, user_id)

    def score_importance(self, text: str) -> float:
        """Return an importance score (0-1) for a single text."""
        importance, _ = self._score_message(text)
        return importance

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _score_message(self, content: str) -> tuple[float, set[str]]:
        """
        Score a message's importance and identify fact types.

        Returns ``(importance_score, set_of_fact_types)``.
        """
        score = 0.0
        fact_types: set[str] = set()
        content_lower = content.lower()

        # Pattern matching
        for fact_type, pattern in _FACT_PATTERNS:
            if pattern.search(content):
                score += 0.3
                fact_types.add(fact_type)

        # Keyword boosting
        words = set(re.findall(r"[a-z]+", content_lower))
        keyword_hits = words & _IMPORTANCE_KEYWORDS
        score += len(keyword_hits) * 0.1

        # Length bonus (longer messages often contain more substance)
        word_count = len(content.split())
        if word_count > 20:
            score += 0.05
        if word_count > 50:
            score += 0.05

        # Cap at 1.0
        return min(score, 1.0), fact_types

    def _extract_key_sentences(self, content: str, fact_types: set[str]) -> str:
        """
        Extract the most relevant sentences from a message based on the
        detected fact types.
        """
        sentences = re.split(r'(?<=[.!?])\s+', content)
        if len(sentences) <= 2:
            return content

        scored: list[tuple[float, str]] = []
        for sent in sentences:
            s = 0.0
            for fact_type, pattern in _FACT_PATTERNS:
                if fact_type in fact_types and pattern.search(sent):
                    s += 1.0
            words = set(re.findall(r"[a-z]+", sent.lower()))
            s += len(words & _IMPORTANCE_KEYWORDS) * 0.5
            scored.append((s, sent))

        scored.sort(key=lambda x: x[0], reverse=True)
        # Take top sentences (at least 1, at most 3)
        top = [s for _, s in scored[:3] if _ > 0]
        if not top:
            top = [scored[0][1]] if scored else [content]

        return " ".join(top)

    def _parse_llm_facts(
        self,
        response: str,
        conversation_id: Optional[str],
        user_id: Optional[str],
    ) -> list[dict]:
        """Parse the LLM's structured fact extraction response."""
        facts: list[dict] = []
        now = datetime.now(timezone.utc).isoformat()
        valid_types = {"decision", "preference", "goal", "brand_guideline", "instruction", "fact"}

        for line in response.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            # Try to parse "TYPE: text"
            match = re.match(r"^(\w+):\s*(.+)$", line)
            if match:
                fact_type = match.group(1).lower().replace(" ", "_")
                fact_text = match.group(2).strip()
                if fact_type not in valid_types:
                    fact_type = "fact"
                metadata = {
                    "type": fact_type,
                    "timestamp": now,
                    "source": "memory_watcher_llm",
                    "importance": 0.8,
                }
                if conversation_id:
                    metadata["conversation_id"] = conversation_id
                if user_id:
                    metadata["user_id"] = user_id
                facts.append({"text": fact_text, "metadata": metadata})

        return facts
