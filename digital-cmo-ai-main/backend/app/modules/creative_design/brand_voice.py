"""
Brand Voice Learning System for the Creative & Design Module.

Extracts, stores, and applies brand voice characteristics from
user-provided examples. Analyses writing samples to build a
brand voice profile that can be injected into copy generation prompts.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BrandVoiceProfile:
    """Structured representation of a brand's writing voice."""

    brand_name: str
    tone_attributes: list[str] = field(default_factory=list)
    vocabulary_preferences: list[str] = field(default_factory=list)
    vocabulary_avoid: list[str] = field(default_factory=list)
    sentence_style: str = ""
    personality_traits: list[str] = field(default_factory=list)
    target_audience: str = ""
    values: list[str] = field(default_factory=list)
    dos: list[str] = field(default_factory=list)
    donts: list[str] = field(default_factory=list)
    example_phrases: list[str] = field(default_factory=list)
    raw_analysis: str = ""

    def to_dict(self) -> dict:
        return {
            "brand_name": self.brand_name,
            "tone_attributes": self.tone_attributes,
            "vocabulary_preferences": self.vocabulary_preferences,
            "vocabulary_avoid": self.vocabulary_avoid,
            "sentence_style": self.sentence_style,
            "personality_traits": self.personality_traits,
            "target_audience": self.target_audience,
            "values": self.values,
            "dos": self.dos,
            "donts": self.donts,
            "example_phrases": self.example_phrases,
        }

    def to_prompt_fragment(self) -> str:
        """Convert the profile into a prompt fragment for copy generation."""
        sections = [f"Brand: {self.brand_name}"]

        if self.tone_attributes:
            sections.append(f"Tone: {', '.join(self.tone_attributes)}")
        if self.personality_traits:
            sections.append(f"Personality: {', '.join(self.personality_traits)}")
        if self.target_audience:
            sections.append(f"Target audience: {self.target_audience}")
        if self.values:
            sections.append(f"Core values: {', '.join(self.values)}")
        if self.vocabulary_preferences:
            sections.append(f"Preferred vocabulary: {', '.join(self.vocabulary_preferences)}")
        if self.vocabulary_avoid:
            sections.append(f"Avoid these words/phrases: {', '.join(self.vocabulary_avoid)}")
        if self.sentence_style:
            sections.append(f"Sentence style: {self.sentence_style}")
        if self.dos:
            sections.append("Do: " + "; ".join(self.dos))
        if self.donts:
            sections.append("Don't: " + "; ".join(self.donts))
        if self.example_phrases:
            sections.append("Example phrases that capture the voice: " + " | ".join(self.example_phrases[:5]))

        return "\n".join(sections)

    @classmethod
    def from_dict(cls, data: dict) -> "BrandVoiceProfile":
        """Construct a profile from a dictionary."""
        return cls(
            brand_name=data.get("brand_name", "Unknown"),
            tone_attributes=data.get("tone_attributes", []),
            vocabulary_preferences=data.get("vocabulary_preferences", []),
            vocabulary_avoid=data.get("vocabulary_avoid", []),
            sentence_style=data.get("sentence_style", ""),
            personality_traits=data.get("personality_traits", []),
            target_audience=data.get("target_audience", ""),
            values=data.get("values", []),
            dos=data.get("dos", []),
            donts=data.get("donts", []),
            example_phrases=data.get("example_phrases", []),
        )


VOICE_ANALYSIS_PROMPT = """You are a brand strategist and linguistic analyst. Analyse the following
writing samples to extract a detailed brand voice profile.

WRITING SAMPLES:
{samples}

BRAND NAME: {brand_name}

Analyse the samples and extract:
1. **Tone attributes** (3-5 adjectives describing the overall tone)
2. **Vocabulary preferences** (5-10 characteristic words/phrases the brand uses)
3. **Vocabulary to avoid** (5-10 words/phrases that would feel off-brand)
4. **Sentence style** (short/long, simple/complex, active/passive)
5. **Personality traits** (3-5 traits as if the brand were a person)
6. **Target audience** (who the writing seems aimed at)
7. **Core values** (3-5 values reflected in the writing)
8. **Dos** (5 things a writer should do to match this voice)
9. **Don'ts** (5 things a writer should avoid)
10. **Example phrases** (5 short phrases that capture the brand voice)

Return ONLY valid JSON with this structure:
{{
  "brand_name": "{brand_name}",
  "tone_attributes": [...],
  "vocabulary_preferences": [...],
  "vocabulary_avoid": [...],
  "sentence_style": "...",
  "personality_traits": [...],
  "target_audience": "...",
  "values": [...],
  "dos": [...],
  "donts": [...],
  "example_phrases": [...]
}}
"""

VOICE_CONSISTENCY_PROMPT = """You are a brand voice editor. Check if the following copy is consistent
with the brand voice profile.

BRAND VOICE PROFILE:
{profile}

COPY TO CHECK:
{copy_text}

Evaluate the copy on these dimensions (score 0-100 each):
1. Tone alignment
2. Vocabulary consistency
3. Sentence style match
4. Personality reflection
5. Overall brand voice score

Provide specific suggestions for improvement.

Return ONLY valid JSON:
{{
  "scores": {{
    "tone_alignment": 85,
    "vocabulary_consistency": 70,
    "sentence_style_match": 80,
    "personality_reflection": 75,
    "overall": 78
  }},
  "suggestions": ["...", "..."],
  "revised_copy": "..."
}}
"""


class BrandVoiceLearner:
    """
    Extracts and manages brand voice profiles from user-provided examples.
    """

    def __init__(self, llm_client=None, memory_manager=None):
        self.llm = llm_client
        self.memory = memory_manager
        self._profiles: dict[str, BrandVoiceProfile] = {}

    async def learn_voice(
        self,
        brand_name: str,
        samples: list[str],
    ) -> BrandVoiceProfile:
        """
        Analyse writing samples and build a brand voice profile.

        Args:
            brand_name: Name of the brand.
            samples: List of writing samples (marketing copy, blog posts, etc.).

        Returns:
            A BrandVoiceProfile object.
        """
        samples_text = "\n\n---\n\n".join(
            f"Sample {i+1}:\n{s}" for i, s in enumerate(samples)
        )

        prompt = VOICE_ANALYSIS_PROMPT.format(
            samples=samples_text,
            brand_name=brand_name,
        )

        raw = await self._call_llm(prompt)
        profile = self._parse_profile(raw, brand_name)

        # Store the profile
        self._profiles[brand_name.lower()] = profile

        # Persist to memory if available
        if self.memory:
            try:
                self.memory.write_to_folder(
                    f"knowledge_base/brand_voice_{brand_name.lower().replace(' ', '_')}.json",
                    json.dumps(profile.to_dict(), indent=2),
                )
            except Exception:
                pass

        return profile

    async def check_consistency(
        self,
        brand_name: str,
        copy_text: str,
    ) -> dict:
        """
        Check if a piece of copy is consistent with the brand voice.

        Args:
            brand_name: Name of the brand to check against.
            copy_text: The copy to evaluate.

        Returns:
            Dict with scores, suggestions, and optionally revised copy.
        """
        profile = self.get_profile(brand_name)
        if not profile:
            return {
                "error": f"No brand voice profile found for '{brand_name}'. "
                         "Please run learn_voice first.",
                "scores": {},
                "suggestions": [],
            }

        prompt = VOICE_CONSISTENCY_PROMPT.format(
            profile=profile.to_prompt_fragment(),
            copy_text=copy_text,
        )

        raw = await self._call_llm(prompt)
        try:
            cleaned = self._extract_json(raw)
            result = json.loads(cleaned)
            if not isinstance(result, dict) or "scores" not in result:
                raise ValueError("Invalid consistency check response.")
        except (json.JSONDecodeError, TypeError, ValueError):
            result = {
                "scores": {"overall": 50},
                "suggestions": ["Unable to parse detailed analysis."],
                "revised_copy": copy_text,
            }

        return result

    def get_profile(self, brand_name: str) -> Optional[BrandVoiceProfile]:
        """Retrieve a stored brand voice profile."""
        profile = self._profiles.get(brand_name.lower())
        if profile:
            return profile

        # Try loading from memory
        if self.memory:
            try:
                stored = self.memory.read_from_folder(
                    f"knowledge_base/brand_voice_{brand_name.lower().replace(' ', '_')}.json"
                )
                if stored:
                    data = json.loads(stored)
                    profile = BrandVoiceProfile.from_dict(data)
                    self._profiles[brand_name.lower()] = profile
                    return profile
            except Exception:
                pass

        return None

    def list_profiles(self) -> list[str]:
        """Return names of all stored brand voice profiles."""
        return list(self._profiles.keys())

    def get_guidelines_for_copy(self, brand_name: str) -> str:
        """
        Return brand guidelines as a string suitable for copy generation prompts.
        Falls back to generic guidelines if no profile exists.
        """
        profile = self.get_profile(brand_name)
        if profile:
            return profile.to_prompt_fragment()
        return "No specific brand voice guidelines available."

    def _parse_profile(self, raw: str, brand_name: str) -> BrandVoiceProfile:
        """Parse LLM output into a BrandVoiceProfile."""
        try:
            cleaned = self._extract_json(raw)
            data = json.loads(cleaned)
            data["brand_name"] = brand_name
            profile = BrandVoiceProfile.from_dict(data)
            profile.raw_analysis = raw
            return profile
        except (json.JSONDecodeError, TypeError):
            # Return a minimal profile
            return BrandVoiceProfile(
                brand_name=brand_name,
                tone_attributes=["professional"],
                raw_analysis=raw,
            )

    @staticmethod
    def _extract_json(text: str) -> str:
        """Extract JSON from text that may contain markdown fences."""
        text = re.sub(r"```(?:json)?\s*", "", text)
        text = re.sub(r"```", "", text)
        start = min(
            (text.find("{"), text.find("[")),
            key=lambda x: x if x >= 0 else float("inf"),
        )
        if start < 0 or start == float("inf"):
            return text.strip()
        opener = text[start]
        closer = "}" if opener == "{" else "]"
        end = text.rfind(closer)
        if end < 0:
            return text.strip()
        return text[start : end + 1]

    async def _call_llm(self, prompt: str) -> str:
        """Call the LLM."""
        if self.llm:
            try:
                messages = [
                    {"role": "system", "content": "You are a brand strategist and linguistic analyst. Always return valid JSON when asked."},
                    {"role": "user", "content": prompt},
                ]
                return await self.llm.generate(messages)
            except Exception as e:
                return f"[Brand Voice Error: {str(e)}]"
        # Demo mode
        return json.dumps({
            "brand_name": "Demo Brand",
            "tone_attributes": ["professional", "approachable", "innovative"],
            "vocabulary_preferences": ["empower", "transform", "seamless"],
            "vocabulary_avoid": ["cheap", "basic", "simply"],
            "sentence_style": "Medium-length, active voice, clear and direct",
            "personality_traits": ["confident", "helpful", "forward-thinking"],
            "target_audience": "Business professionals and decision-makers",
            "values": ["innovation", "transparency", "customer success"],
            "dos": ["Use active voice", "Lead with benefits", "Be specific with data"],
            "donts": ["Use jargon without explanation", "Be overly casual", "Make unsubstantiated claims"],
            "example_phrases": ["Transform your workflow", "Built for teams that move fast", "See the difference in days, not months"],
        })
