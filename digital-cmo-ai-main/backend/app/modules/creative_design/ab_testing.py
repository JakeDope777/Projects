"""
A/B Testing Engine for the Creative & Design Module.

Generates 3-5 copy variants from a base piece, scores each variant on
multiple copywriting dimensions, and returns a ranked list with
explanations and predicted performance metrics.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Optional

from .tone_presets import TonePreset, get_tone


# ── Scoring Dimensions ──────────────────────────────────────────────────

SCORING_DIMENSIONS = [
    {
        "name": "clarity",
        "weight": 0.20,
        "description": "How clear and easy to understand the message is.",
    },
    {
        "name": "emotional_appeal",
        "weight": 0.20,
        "description": "How well the copy triggers an emotional response.",
    },
    {
        "name": "call_to_action_strength",
        "weight": 0.20,
        "description": "How compelling and specific the CTA is.",
    },
    {
        "name": "uniqueness",
        "weight": 0.15,
        "description": "How differentiated the copy is from generic alternatives.",
    },
    {
        "name": "brand_alignment",
        "weight": 0.15,
        "description": "How well the copy aligns with brand voice and guidelines.",
    },
    {
        "name": "scannability",
        "weight": 0.10,
        "description": "How easy it is to skim and extract key information.",
    },
]


@dataclass
class ABVariant:
    """A single A/B test variant with its metadata and scores."""

    variant_id: str
    label: str
    copy_text: str
    strategy: str
    tone_used: str
    dimension_scores: dict[str, float] = field(default_factory=dict)
    overall_score: float = 0.0
    predicted_ctr_lift: float = 0.0
    explanation: str = ""

    def to_dict(self) -> dict:
        return {
            "variant_id": self.variant_id,
            "label": self.label,
            "copy_text": self.copy_text,
            "strategy": self.strategy,
            "tone_used": self.tone_used,
            "dimension_scores": self.dimension_scores,
            "overall_score": round(self.overall_score, 2),
            "predicted_ctr_lift": f"{self.predicted_ctr_lift:+.1f}%",
            "explanation": self.explanation,
        }


# ── Variant Generation Strategies ───────────────────────────────────────

VARIANT_STRATEGIES = [
    {
        "id": "headline_rewrite",
        "label": "Headline Rewrite",
        "instruction": (
            "Rewrite the headline / opening hook to be more attention-grabbing. "
            "Keep the body and CTA similar but adjust the opening to maximise "
            "click-through rate."
        ),
    },
    {
        "id": "tone_shift",
        "label": "Tone Shift",
        "instruction": (
            "Rewrite the copy with a noticeably different tone (e.g. if the "
            "original is formal, make it conversational; if playful, make it "
            "authoritative). Preserve the core message."
        ),
    },
    {
        "id": "cta_variation",
        "label": "CTA Variation",
        "instruction": (
            "Keep the body copy largely the same but create a significantly "
            "different call-to-action. Experiment with urgency, benefit-driven, "
            "or curiosity-based CTAs."
        ),
    },
    {
        "id": "length_variation",
        "label": "Length Variation",
        "instruction": (
            "Create a shorter (or longer) version of the copy. If the original "
            "is long, condense it to its most impactful elements. If short, "
            "expand with supporting details."
        ),
    },
    {
        "id": "social_proof",
        "label": "Social Proof Focus",
        "instruction": (
            "Rewrite the copy to lead with social proof — numbers, testimonials, "
            "authority endorsements, or 'join X others' framing. Make credibility "
            "the primary persuasion lever."
        ),
    },
]


AB_GENERATION_PROMPT = """You are an expert conversion copywriter running A/B tests.

Given the BASE COPY below, generate {num_variants} alternative variants.
Each variant should follow a specific strategy.

BASE COPY:
{base_copy}

VARIANT STRATEGIES (generate one variant per strategy):
{strategies_text}

BRAND GUIDELINES:
{guidelines}

For EACH variant, return a JSON object with these fields:
- "variant_id": strategy id
- "label": strategy label
- "copy_text": the rewritten copy
- "strategy": brief description of what you changed and why
- "tone_used": the tone you used

Return a JSON array of variant objects. Output ONLY valid JSON, no markdown fences.
"""

AB_SCORING_PROMPT = """You are a marketing analytics expert. Score the following copy variant
on each dimension from 0 to 100.

COPY:
{copy_text}

SCORING DIMENSIONS:
{dimensions_text}

For each dimension, provide:
- A score from 0-100
- A one-sentence justification

Also provide:
- An overall weighted score (0-100)
- A predicted CTR lift percentage compared to average copy (-20% to +40%)
- A brief overall explanation (2-3 sentences)

Return ONLY valid JSON with this structure:
{{
  "dimension_scores": {{"clarity": 85, "emotional_appeal": 70, ...}},
  "overall_score": 78.5,
  "predicted_ctr_lift": 12.5,
  "explanation": "..."
}}
"""


class ABTestingEngine:
    """
    Generates and scores A/B test variants for marketing copy.
    """

    def __init__(self, llm_client=None):
        self.llm = llm_client

    async def generate_variants(
        self,
        base_copy: str,
        num_variants: int = 4,
        guidelines: str = "",
        strategies: Optional[list[str]] = None,
    ) -> list[ABVariant]:
        """
        Generate *num_variants* alternative versions of *base_copy*.

        Args:
            base_copy: The original marketing copy.
            num_variants: Number of variants to generate (3-5).
            guidelines: Brand guidelines to respect.
            strategies: Optional list of strategy IDs to use.

        Returns:
            List of ABVariant objects (unscored).
        """
        num_variants = max(3, min(num_variants, 5))

        # Select strategies
        if strategies:
            selected = [s for s in VARIANT_STRATEGIES if s["id"] in strategies]
        else:
            selected = VARIANT_STRATEGIES[:num_variants]

        strategies_text = "\n".join(
            f"{i+1}. [{s['id']}] {s['label']}: {s['instruction']}"
            for i, s in enumerate(selected)
        )

        prompt = AB_GENERATION_PROMPT.format(
            num_variants=len(selected),
            base_copy=base_copy,
            strategies_text=strategies_text,
            guidelines=guidelines or "No specific guidelines.",
        )

        raw = await self._call_llm(prompt)
        variants = self._parse_variants(raw, selected)
        return variants

    async def score_variant(self, variant: ABVariant) -> ABVariant:
        """Score a single variant on all dimensions."""
        dimensions_text = "\n".join(
            f"- {d['name']} (weight {d['weight']:.0%}): {d['description']}"
            for d in SCORING_DIMENSIONS
        )

        prompt = AB_SCORING_PROMPT.format(
            copy_text=variant.copy_text,
            dimensions_text=dimensions_text,
        )

        raw = await self._call_llm(prompt)
        scores = self._parse_scores(raw)

        variant.dimension_scores = scores.get("dimension_scores", {})
        variant.overall_score = scores.get("overall_score", 50.0)
        variant.predicted_ctr_lift = scores.get("predicted_ctr_lift", 0.0)
        variant.explanation = scores.get("explanation", "")
        return variant

    async def generate_and_score(
        self,
        base_copy: str,
        num_variants: int = 4,
        guidelines: str = "",
    ) -> dict:
        """
        Full pipeline: generate variants, score each, and return ranked results.

        Returns:
            Dict with 'base_copy', 'variants' (sorted by score desc), and 'summary'.
        """
        variants = await self.generate_variants(
            base_copy=base_copy,
            num_variants=num_variants,
            guidelines=guidelines,
        )

        scored = []
        for v in variants:
            scored_v = await self.score_variant(v)
            scored.append(scored_v)

        # Sort by overall score descending
        scored.sort(key=lambda v: v.overall_score, reverse=True)

        return {
            "base_copy": base_copy,
            "num_variants": len(scored),
            "variants": [v.to_dict() for v in scored],
            "recommended_variant": scored[0].to_dict() if scored else None,
            "scoring_dimensions": SCORING_DIMENSIONS,
            "summary": self._build_summary(scored),
        }

    # ── Internal helpers ────────────────────────────────────────────────

    def _parse_variants(self, raw: str, strategies: list[dict]) -> list[ABVariant]:
        """Parse LLM JSON output into ABVariant objects."""
        try:
            # Try to extract JSON from the response
            cleaned = self._extract_json(raw)
            data = json.loads(cleaned)
            if not isinstance(data, list):
                data = [data]
        except (json.JSONDecodeError, TypeError):
            # Fallback: create placeholder variants
            data = []
            for i, s in enumerate(strategies):
                data.append({
                    "variant_id": s["id"],
                    "label": s["label"],
                    "copy_text": f"[Variant {i+1}] {raw[:200]}",
                    "strategy": s["instruction"][:100],
                    "tone_used": "professional",
                })

        variants = []
        for i, item in enumerate(data):
            fallback_strategy = strategies[i] if i < len(strategies) else strategies[-1]
            variants.append(ABVariant(
                variant_id=item.get("variant_id", fallback_strategy["id"]),
                label=item.get("label", fallback_strategy["label"]),
                copy_text=item.get("copy_text", ""),
                strategy=item.get("strategy", ""),
                tone_used=item.get("tone_used", "professional"),
            ))

        return variants

    def _parse_scores(self, raw: str) -> dict:
        """Parse LLM scoring output into a scores dict."""
        try:
            cleaned = self._extract_json(raw)
            data = json.loads(cleaned)
            if not isinstance(data, dict):
                raise ValueError("Expected a JSON object for scores.")
            return data
        except (json.JSONDecodeError, TypeError, ValueError):
            # Return default scores
            return {
                "dimension_scores": {d["name"]: 50.0 for d in SCORING_DIMENSIONS},
                "overall_score": 50.0,
                "predicted_ctr_lift": 0.0,
                "explanation": "Scoring unavailable — using default values.",
            }

    @staticmethod
    def _extract_json(text: str) -> str:
        """Extract JSON from a string that may contain markdown fences or extra text."""
        # Remove markdown code fences
        text = re.sub(r"```(?:json)?\s*", "", text)
        text = re.sub(r"```", "", text)
        # Find the first [ or { and last ] or }
        start_bracket = min(
            (text.find("["), text.find("{")),
            key=lambda x: x if x >= 0 else float("inf"),
        )
        if start_bracket < 0 or start_bracket == float("inf"):
            return text.strip()
        opener = text[start_bracket]
        closer = "]" if opener == "[" else "}"
        end_bracket = text.rfind(closer)
        if end_bracket < 0:
            return text.strip()
        return text[start_bracket : end_bracket + 1]

    @staticmethod
    def _build_summary(variants: list[ABVariant]) -> str:
        """Build a human-readable summary of the A/B test results."""
        if not variants:
            return "No variants were generated."
        best = variants[0]
        lines = [
            f"Generated {len(variants)} variants. "
            f"Recommended: '{best.label}' (score: {best.overall_score:.1f}/100, "
            f"predicted CTR lift: {best.predicted_ctr_lift:+.1f}%).",
        ]
        for i, v in enumerate(variants, 1):
            lines.append(
                f"  {i}. {v.label} — Score: {v.overall_score:.1f}, "
                f"CTR lift: {v.predicted_ctr_lift:+.1f}%"
            )
        return "\n".join(lines)

    async def _call_llm(self, prompt: str) -> str:
        """Call the LLM with a prompt."""
        if self.llm:
            try:
                messages = [
                    {"role": "system", "content": "You are an expert marketing copywriter and conversion optimisation specialist. Always return valid JSON when asked."},
                    {"role": "user", "content": prompt},
                ]
                return await self.llm.generate(messages)
            except Exception as e:
                return f"[AB Testing Error: {str(e)}]"
        # Demo mode fallback
        return json.dumps([
            {
                "variant_id": s["id"],
                "label": s["label"],
                "copy_text": f"[Demo variant for {s['label']}]",
                "strategy": s["instruction"][:80],
                "tone_used": "professional",
            }
            for s in VARIANT_STRATEGIES[:4]
        ])
