"""
Tone & Style Presets for Creative Copy Generation.

Defines reusable tone profiles that shape how marketing copy reads and feels.
Each preset includes a system-level instruction, vocabulary guidance, and
structural hints that are injected into LLM prompts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class TonePreset:
    """Immutable description of a writing tone / style."""

    name: str
    description: str
    system_instruction: str
    vocabulary_hints: list[str] = field(default_factory=list)
    sentence_style: str = "mixed"
    emoji_allowed: bool = False
    max_exclamation_marks: int = 1

    def to_prompt_fragment(self) -> str:
        """Return a prompt fragment that can be prepended to any copy brief."""
        vocab = ", ".join(self.vocabulary_hints) if self.vocabulary_hints else "general business vocabulary"
        return (
            f"Tone: {self.name} — {self.description}\n"
            f"Writing instructions: {self.system_instruction}\n"
            f"Preferred vocabulary: {vocab}\n"
            f"Sentence style: {self.sentence_style}\n"
            f"Emoji usage: {'allowed sparingly' if self.emoji_allowed else 'not allowed'}\n"
        )


# ── Built-in Presets ────────────────────────────────────────────────────

PROFESSIONAL = TonePreset(
    name="professional",
    description="Polished, authoritative, and business-appropriate.",
    system_instruction=(
        "Write in a clear, confident, and polished tone. Use precise language, "
        "avoid slang, and maintain a formal yet approachable register. "
        "Prioritise clarity and credibility."
    ),
    vocabulary_hints=["leverage", "optimize", "strategic", "insights", "drive results"],
    sentence_style="medium-to-long, well-structured paragraphs",
    emoji_allowed=False,
    max_exclamation_marks=0,
)

PLAYFUL = TonePreset(
    name="playful",
    description="Fun, light-hearted, and energetic.",
    system_instruction=(
        "Write in a fun, upbeat, and conversational tone. Use wordplay, "
        "light humour, and short punchy sentences. Feel free to break "
        "conventional grammar rules for effect."
    ),
    vocabulary_hints=["awesome", "game-changer", "love", "vibe", "level-up"],
    sentence_style="short and punchy with occasional fragments",
    emoji_allowed=True,
    max_exclamation_marks=3,
)

URGENT = TonePreset(
    name="urgent",
    description="Time-sensitive, action-oriented, and compelling.",
    system_instruction=(
        "Write with urgency and a strong call-to-action. Use imperative verbs, "
        "scarcity language, and short declarative sentences. Create a sense of "
        "FOMO (fear of missing out) without being manipulative."
    ),
    vocabulary_hints=["now", "limited", "don't miss", "act fast", "last chance", "today only"],
    sentence_style="short, direct, imperative",
    emoji_allowed=False,
    max_exclamation_marks=2,
)

EMPATHETIC = TonePreset(
    name="empathetic",
    description="Warm, understanding, and human-centred.",
    system_instruction=(
        "Write with warmth, empathy, and genuine understanding. Acknowledge "
        "the reader's challenges before presenting solutions. Use inclusive "
        "language and a supportive, encouraging tone."
    ),
    vocabulary_hints=["we understand", "you deserve", "together", "support", "care"],
    sentence_style="medium length, warm and flowing",
    emoji_allowed=False,
    max_exclamation_marks=1,
)

AUTHORITATIVE = TonePreset(
    name="authoritative",
    description="Expert, data-driven, and thought-leadership oriented.",
    system_instruction=(
        "Write as a recognised industry expert. Reference data, trends, and "
        "best practices. Use confident, declarative statements and back claims "
        "with evidence. Maintain a scholarly yet accessible register."
    ),
    vocabulary_hints=["research shows", "data indicates", "industry-leading", "proven", "benchmark"],
    sentence_style="longer, well-supported sentences with evidence",
    emoji_allowed=False,
    max_exclamation_marks=0,
)

CONVERSATIONAL = TonePreset(
    name="conversational",
    description="Casual, friendly, and relatable — like talking to a friend.",
    system_instruction=(
        "Write as if you're having a friendly chat with the reader. Use "
        "contractions, rhetorical questions, and first/second person pronouns. "
        "Keep it real and relatable."
    ),
    vocabulary_hints=["hey", "you know", "let's", "honestly", "right?"],
    sentence_style="short to medium, informal, with questions",
    emoji_allowed=True,
    max_exclamation_marks=2,
)

# ── Registry ────────────────────────────────────────────────────────────

TONE_REGISTRY: dict[str, TonePreset] = {
    "professional": PROFESSIONAL,
    "playful": PLAYFUL,
    "urgent": URGENT,
    "empathetic": EMPATHETIC,
    "authoritative": AUTHORITATIVE,
    "conversational": CONVERSATIONAL,
}


def get_tone(name: str) -> TonePreset:
    """Return a tone preset by name, falling back to *professional*."""
    return TONE_REGISTRY.get(name.lower(), PROFESSIONAL)


def list_tones() -> list[str]:
    """Return all available tone names."""
    return list(TONE_REGISTRY.keys())


def register_custom_tone(preset: TonePreset) -> None:
    """Register a user-defined tone preset at runtime."""
    TONE_REGISTRY[preset.name.lower()] = preset
