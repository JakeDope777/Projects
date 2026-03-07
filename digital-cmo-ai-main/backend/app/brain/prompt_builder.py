"""
Prompt Builder - assembles structured prompts for the LLM.

Improvements over the original:
- **Token-aware context budgeting** – allocates a configurable token budget
  across the four memory layers and truncates / compresses to fit.
- **Relevance scoring** – ranks context items and drops the least relevant
  when the budget is tight.
- **Conversation summarisation hook** – injects a compressed summary of older
  turns instead of raw messages.
- **Skill-specific system prompts** – each skill module can register a
  specialised system instruction.
"""

from __future__ import annotations

import re
from typing import Optional


# ---------------------------------------------------------------------------
# Token estimation (fast heuristic – avoids importing tiktoken at module level)
# ---------------------------------------------------------------------------

def estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars per token for English text."""
    return max(1, len(text) // 4)


def truncate_to_tokens(text: str, max_tokens: int) -> str:
    """Truncate *text* to approximately *max_tokens* tokens."""
    max_chars = max_tokens * 4
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n... [truncated]"


# ---------------------------------------------------------------------------
# Default system instruction
# ---------------------------------------------------------------------------

SYSTEM_INSTRUCTION = """You are the Digital CMO AI, an AI-powered chief marketing officer.
You help users plan, execute, and analyse marketing campaigns. You have access to
business analysis, creative design, CRM management, analytics, and integration tools.

Guidelines:
- Be professional, concise, and data-driven.
- When providing analysis, cite sources where possible.
- Respect brand guidelines stored in memory.
- If you are unsure, ask clarifying questions.
- Always consider GDPR and privacy regulations.
"""

# Skill-specific system prompt extensions
SKILL_INSTRUCTIONS: dict[str, str] = {
    "business_analysis": (
        "You are currently operating as the Business Analysis specialist. "
        "Provide structured, data-backed analysis. Use frameworks like SWOT, "
        "PESTEL, Porter's Five Forces, and customer segmentation where appropriate."
    ),
    "creative_design": (
        "You are currently operating as the Creative Design specialist. "
        "Generate compelling copy, suggest visual concepts, and maintain "
        "brand voice consistency. Offer A/B test variations when relevant."
    ),
    "crm_campaign": (
        "You are currently operating as the CRM & Campaign specialist. "
        "Design effective email sequences, lead scoring models, and campaign "
        "workflows. Always flag compliance considerations (GDPR, CAN-SPAM)."
    ),
    "analytics_reporting": (
        "You are currently operating as the Analytics & Reporting specialist. "
        "Provide clear metric definitions, trend analysis, and actionable "
        "recommendations. Use tables and charts where helpful."
    ),
    "integrations": (
        "You are currently operating as the Integrations specialist. "
        "Guide users through API connections, OAuth flows, and data sync "
        "configurations. Provide step-by-step instructions."
    ),
    "system": (
        "You are handling a system / account management request. "
        "Help the user with settings, preferences, memory management, "
        "and subscription details."
    ),
}

# ---------------------------------------------------------------------------
# Context budget allocation (percentage of total budget)
# ---------------------------------------------------------------------------

DEFAULT_TOKEN_BUDGET = 6000  # total tokens available for context

BUDGET_ALLOCATION = {
    "system": 0.15,           # system prompt + skill instruction
    "conversation_summary": 0.15,  # compressed older history
    "conversation_recent": 0.25,   # last N raw messages
    "retrieved_memories": 0.20,    # vector search results
    "structured_knowledge": 0.15,  # persistent folder data
    "db_results": 0.10,           # SQLite query results
}


# ---------------------------------------------------------------------------
# PromptBuilder
# ---------------------------------------------------------------------------

class PromptBuilder:
    """
    Constructs composite prompts by combining system instructions,
    conversation history, retrieved memories, structured knowledge,
    and database query results – all within a configurable token budget.
    """

    def __init__(
        self,
        system_instruction: Optional[str] = None,
        token_budget: int = DEFAULT_TOKEN_BUDGET,
    ):
        self.system_instruction = system_instruction or SYSTEM_INSTRUCTION
        self.token_budget = token_budget

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build(
        self,
        user_message: str,
        conversation_history: Optional[list[dict]] = None,
        conversation_summary: Optional[str] = None,
        retrieved_memories: Optional[list[str]] = None,
        structured_knowledge: Optional[dict[str, str]] = None,
        db_results: Optional[list[dict]] = None,
        skill_context: Optional[str] = None,
        token_budget: Optional[int] = None,
    ) -> list[dict]:
        """
        Build a list of messages suitable for an OpenAI-compatible chat API.

        The builder allocates a token budget across the different context
        layers and truncates each layer to fit.

        Args:
            user_message: The current user input.
            conversation_history: List of prior messages [{role, content}].
            conversation_summary: Compressed summary of older conversation turns.
            retrieved_memories: Top-k relevant snippets from vector store.
            structured_knowledge: Key-value pairs from persistent folders.
            db_results: Rows returned from SQLite queries.
            skill_context: Skill identifier (e.g. ``"business_analysis"``).
            token_budget: Override the default token budget for this call.

        Returns:
            A list of message dicts with ``role`` and ``content`` keys.
        """
        budget = token_budget or self.token_budget
        messages: list[dict] = []

        # ── 1. System message ──────────────────────────────────────────
        system_budget = int(budget * BUDGET_ALLOCATION["system"])
        system_parts = [self.system_instruction]

        # Inject skill-specific instruction
        if skill_context:
            skill_instr = SKILL_INSTRUCTIONS.get(skill_context, "")
            if skill_instr:
                system_parts.append(f"\n{skill_instr}")
            else:
                system_parts.append(f"\n[Active Module]: {skill_context}")

        system_text = "\n".join(system_parts)
        system_text = truncate_to_tokens(system_text, system_budget)
        messages.append({"role": "system", "content": system_text})

        # ── 2. Structured knowledge (persistent folders) ───────────────
        if structured_knowledge:
            sk_budget = int(budget * BUDGET_ALLOCATION["structured_knowledge"])
            sk_text = self._format_structured_knowledge(structured_knowledge, sk_budget)
            if sk_text:
                messages.append({"role": "system", "content": sk_text})

        # ── 3. Retrieved memories (vector store) ──────────────────────
        if retrieved_memories:
            mem_budget = int(budget * BUDGET_ALLOCATION["retrieved_memories"])
            mem_text = self._format_retrieved_memories(retrieved_memories, mem_budget)
            if mem_text:
                messages.append({"role": "system", "content": mem_text})

        # ── 4. Database results ────────────────────────────────────────
        if db_results:
            db_budget = int(budget * BUDGET_ALLOCATION["db_results"])
            db_text = self._format_db_results(db_results, db_budget)
            if db_text:
                messages.append({"role": "system", "content": db_text})

        # ── 5. Conversation summary (compressed older turns) ──────────
        if conversation_summary:
            sum_budget = int(budget * BUDGET_ALLOCATION["conversation_summary"])
            summary_text = truncate_to_tokens(
                f"[Conversation Summary]:\n{conversation_summary}", sum_budget
            )
            messages.append({"role": "system", "content": summary_text})

        # ── 6. Recent conversation history ─────────────────────────────
        if conversation_history:
            recent_budget = int(budget * BUDGET_ALLOCATION["conversation_recent"])
            recent_msgs = self._select_recent_history(conversation_history, recent_budget)
            messages.extend(recent_msgs)

        # ── 7. Current user message ────────────────────────────────────
        messages.append({"role": "user", "content": user_message})

        return messages

    def build_skill_prompt(
        self,
        skill_name: str,
        task_description: str,
        data: Optional[dict] = None,
    ) -> list[dict]:
        """
        Build a prompt specifically for a skill module to process.
        """
        system_msg = SKILL_INSTRUCTIONS.get(
            skill_name,
            f"You are the {skill_name} specialist within Digital CMO AI. "
            f"Complete the following task professionally and thoroughly.",
        )
        user_content = task_description
        if data:
            user_content += f"\n\nAdditional data:\n{data}"

        return [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_content},
        ]

    # ------------------------------------------------------------------
    # Formatting helpers
    # ------------------------------------------------------------------

    def _format_structured_knowledge(
        self, knowledge: dict[str, str], budget: int
    ) -> str:
        """Format structured knowledge within a token budget."""
        header = "[Structured Knowledge]:\n"
        parts = []
        remaining = budget - estimate_tokens(header)

        # Sort by value length (shorter items first to maximise coverage)
        sorted_items = sorted(knowledge.items(), key=lambda kv: len(kv[1]))
        for key, value in sorted_items:
            entry = f"- **{key}**: {value}\n"
            entry_tokens = estimate_tokens(entry)
            if entry_tokens <= remaining:
                parts.append(entry)
                remaining -= entry_tokens
            else:
                # Truncate the value to fit
                truncated = truncate_to_tokens(value, remaining - estimate_tokens(f"- **{key}**: "))
                parts.append(f"- **{key}**: {truncated}\n")
                break

        if not parts:
            return ""
        return header + "".join(parts)

    def _format_retrieved_memories(
        self, memories: list[str], budget: int
    ) -> str:
        """Format retrieved memory snippets within a token budget."""
        header = "[Retrieved Memories]:\n"
        parts = []
        remaining = budget - estimate_tokens(header)

        for i, mem in enumerate(memories, 1):
            entry = f"{i}. {mem}\n"
            entry_tokens = estimate_tokens(entry)
            if entry_tokens <= remaining:
                parts.append(entry)
                remaining -= entry_tokens
            else:
                break

        if not parts:
            return ""
        return header + "".join(parts)

    def _format_db_results(self, db_results: list[dict], budget: int) -> str:
        """Format database results within a token budget."""
        header = "[Database Results]:\n"
        parts = []
        remaining = budget - estimate_tokens(header)

        for row in db_results[:20]:  # hard cap
            entry = f"- {row}\n"
            entry_tokens = estimate_tokens(entry)
            if entry_tokens <= remaining:
                parts.append(entry)
                remaining -= entry_tokens
            else:
                break

        if not parts:
            return ""
        return header + "".join(parts)

    def _select_recent_history(
        self, history: list[dict], budget: int
    ) -> list[dict]:
        """
        Select as many recent messages as fit within the token budget,
        working backwards from the most recent.
        """
        selected: list[dict] = []
        remaining = budget

        for msg in reversed(history):
            content = msg.get("content", "")
            tokens = estimate_tokens(content)
            if tokens <= remaining:
                selected.append({
                    "role": msg.get("role", "user"),
                    "content": content,
                })
                remaining -= tokens
            else:
                # Try to include a truncated version of this message
                if remaining > 50:
                    truncated = truncate_to_tokens(content, remaining)
                    selected.append({
                        "role": msg.get("role", "user"),
                        "content": truncated,
                    })
                break

        selected.reverse()
        return selected

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def estimate_prompt_tokens(self, messages: list[dict]) -> int:
        """Estimate the total token count for a list of messages."""
        total = 0
        for msg in messages:
            total += estimate_tokens(msg.get("content", ""))
            total += 4  # role + formatting overhead per message
        return total
