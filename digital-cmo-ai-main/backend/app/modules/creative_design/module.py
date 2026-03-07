"""
Creative & Design Module — Expanded Edition
=============================================

Central orchestrator for all creative and design capabilities:

- **Copy generation** across 11 formats (blog posts, social captions, email
  subjects, ad headlines, product descriptions, LinkedIn posts, Twitter/X
  threads, YouTube scripts, press releases, landing page copy, SMS campaigns)
- **Tone / style presets** (professional, playful, urgent, empathetic,
  authoritative, conversational) with custom preset support
- **Image prompt generation** for visual assets
- **A/B test variant generation** with 3-5 scored variants and predicted
  performance metrics
- **Smart content calendar** considering product launches, seasonal events,
  industry events, and optimal posting times per platform
- **Brand voice learning** that extracts and applies voice guidelines from
  user-provided samples
- **Multi-language support** (English, Spanish, French, German, Portuguese)
  with cultural adaptation
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Optional

from .tone_presets import get_tone, list_tones, TonePreset
from .copy_formats import get_format, list_formats, CopyFormat
from .ab_testing import ABTestingEngine
from .content_calendar import ContentCalendarEngine
from .brand_voice import BrandVoiceLearner
from .multilingual import MultilingualEngine, get_language, list_languages


# ── Image Prompt Template ───────────────────────────────────────────────

IMAGE_PROMPT_TEMPLATE = """Create a detailed image generation prompt for:

Description: {description}
Style: {style}
Brand context: {brand_context}

Generate a detailed, specific prompt suitable for an AI image generator.
Focus on composition, colours, mood, and key visual elements.
Do NOT include any real people or identifiable individuals.
Include aspect ratio suggestion and visual hierarchy notes.
"""


class CreativeDesignModule:
    """
    Generates marketing assets including copy, images, A/B test variants,
    content calendars, and manages brand voice profiles.

    This is the main entry point used by the Brain orchestrator and the
    Creative API router.
    """

    def __init__(self, llm_client=None, image_generator=None, memory_manager=None):
        self.llm = llm_client
        self.image_generator = image_generator
        self.memory = memory_manager

        # Sub-engines
        self.ab_engine = ABTestingEngine(llm_client=llm_client)
        self.calendar_engine = ContentCalendarEngine(llm_client=llm_client)
        self.brand_voice = BrandVoiceLearner(llm_client=llm_client, memory_manager=memory_manager)
        self.multilingual = MultilingualEngine(llm_client=llm_client)

    # ── Generic Handler (called by Brain orchestrator) ──────────────────

    async def handle(self, message: str, context: dict) -> dict:
        """Generic handler called by the Brain orchestrator."""
        msg = message.lower()

        if any(kw in msg for kw in ["image", "banner", "visual", "graphic"]):
            result = await self.generate_image(message, context=context)
            return {"response": result.get("content", result.get("image_url", ""))}

        if "a/b" in msg or "ab test" in msg or "variant" in msg:
            result = await self.suggest_ab_tests(message, context=context)
            return {"response": json.dumps(result, indent=2, default=str)}

        if any(kw in msg for kw in ["calendar", "schedule", "plan"]):
            result = await self.create_content_calendar(context=context)
            return {"response": json.dumps(result, indent=2, default=str)}

        if any(kw in msg for kw in ["brand voice", "voice profile", "brand style"]):
            return {"response": "Please use the /creative/brand-voice endpoint with writing samples."}

        if any(kw in msg for kw in ["translate", "translation", "spanish", "french", "german", "portuguese"]):
            result = await self.translate_copy(message, target_language="es", context=context)
            return {"response": result.get("translated", "")}

        # Default: generate copy
        result = await self.generate_copy(message, context=context)
        return {"response": result.get("content", "")}

    # ── Copy Generation ─────────────────────────────────────────────────

    async def generate_copy(
        self,
        brief: str,
        tone: Optional[str] = None,
        copy_format: Optional[str] = None,
        length: Optional[int] = None,
        language: Optional[str] = None,
        brand_name: Optional[str] = None,
        context: Optional[dict] = None,
    ) -> dict:
        """
        Generate marketing copy with full format, tone, language, and brand support.

        Args:
            brief: Description of the desired content.
            tone: Tone preset name (professional, playful, urgent, etc.).
            copy_format: Format name (blog_post, linkedin_post, sms_campaign, etc.).
            length: Approximate word count (overrides format default).
            language: Language code or name (en, es, fr, de, pt).
            brand_name: Brand name for voice guidelines lookup.
            context: Additional context from memory.

        Returns:
            Dict with content, metadata, and alternatives.
        """
        context = context or {}

        # Resolve tone
        tone_preset = get_tone(tone or "professional")
        tone_fragment = tone_preset.to_prompt_fragment()

        # Resolve format
        fmt = get_format(copy_format or "blog_post")
        length = length or fmt.default_length

        # Resolve brand guidelines
        guidelines = self._get_brand_guidelines(brand_name)

        # Resolve language
        lang_code = language or "en"
        lang_profile = get_language(lang_code)

        # Generate in target language if not English
        if lang_profile.code != "en":
            result = await self.multilingual.generate_multilingual(
                brief=brief,
                target_language=lang_code,
                tone_fragment=tone_fragment,
                length=length,
                guidelines=guidelines,
            )
            return {
                "content": result["content"],
                "alternatives": [],
                "metadata": {
                    "tone": tone_preset.name,
                    "format": fmt.name,
                    "length": length,
                    "language": result["language"],
                    "language_name": result["language_name"],
                    "formality": result["formality"],
                },
            }

        # Build English prompt using format template
        prompt = fmt.build_prompt(
            brief=brief,
            tone_fragment=tone_fragment,
            guidelines=guidelines,
            language=lang_profile.name,
        )

        response = await self._call_llm(prompt)

        return {
            "content": response,
            "alternatives": [],
            "metadata": {
                "tone": tone_preset.name,
                "format": fmt.name,
                "length": length,
                "language": lang_profile.code,
                "language_name": lang_profile.name,
            },
        }

    # ── Image Generation ────────────────────────────────────────────────

    async def generate_image(
        self,
        description: str,
        style: Optional[str] = None,
        brand_name: Optional[str] = None,
        context: Optional[dict] = None,
    ) -> dict:
        """
        Generate a visual asset based on description and style.

        Args:
            description: What the image should depict.
            style: Visual style (modern, minimalist, bold, etc.).
            brand_name: Brand name for context.
            context: Additional context.

        Returns:
            Dict with image_url or content describing the image.
        """
        style = style or "modern and professional"
        brand_context = self._get_brand_guidelines(brand_name)

        if self.image_generator:
            try:
                prompt = f"{description}. Style: {style}. No real people."
                image_url = await self.image_generator.generate(prompt)
                return {"image_url": image_url, "content": f"Image generated: {image_url}"}
            except Exception as e:
                return {"content": f"[Image generation error: {str(e)}]"}

        # Fallback: generate a detailed prompt description
        prompt = IMAGE_PROMPT_TEMPLATE.format(
            description=description, style=style, brand_context=brand_context
        )
        response = await self._call_llm(prompt)

        return {
            "content": response,
            "image_url": None,
            "note": "Image generation API not configured. Returning prompt description.",
        }

    # ── A/B Testing ─────────────────────────────────────────────────────

    async def suggest_ab_tests(
        self,
        base_copy: str,
        num_variants: int = 4,
        brand_name: Optional[str] = None,
        context: Optional[dict] = None,
    ) -> dict:
        """
        Generate and score A/B test variants for marketing copy.

        Args:
            base_copy: The original marketing copy.
            num_variants: Number of variants (3-5).
            brand_name: Brand name for guidelines.
            context: Additional context.

        Returns:
            Dict with ranked variants, scores, and recommendations.
        """
        guidelines = self._get_brand_guidelines(brand_name)
        result = await self.ab_engine.generate_and_score(
            base_copy=base_copy,
            num_variants=num_variants,
            guidelines=guidelines,
        )
        return result

    # ── Content Calendar ────────────────────────────────────────────────

    async def create_content_calendar(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        channels: Optional[list[str]] = None,
        industry: Optional[str] = None,
        product_launches: Optional[list[dict]] = None,
        custom_events: Optional[list[dict]] = None,
        brand_name: Optional[str] = None,
        context: Optional[dict] = None,
    ) -> dict:
        """
        Generate a smart content calendar.

        Args:
            start_date: Calendar start (YYYY-MM-DD).
            end_date: Calendar end (YYYY-MM-DD).
            channels: List of channels.
            industry: Industry vertical.
            product_launches: Product launch events.
            custom_events: Additional events.
            brand_name: Brand name for guidelines.
            context: Additional context.

        Returns:
            Dict with calendar entries, events, and metadata.
        """
        guidelines = self._get_brand_guidelines(brand_name)
        result = await self.calendar_engine.generate_calendar(
            start_date=start_date,
            end_date=end_date,
            channels=channels,
            industry=industry,
            product_launches=product_launches,
            custom_events=custom_events,
            brand_guidelines=guidelines,
        )
        return result

    # ── Legacy compatibility: create_content_schedule ────────────────────

    async def create_content_schedule(
        self, events: list[dict], context: Optional[dict] = None
    ) -> dict:
        """
        Legacy method for backward compatibility.
        Converts old-style event list to the new calendar engine.
        """
        product_launches = []
        custom_events = []
        for event in events:
            if event.get("type") == "product_launch":
                product_launches.append(event)
            else:
                custom_events.append(event)

        result = await self.create_content_calendar(
            custom_events=custom_events or events,
            product_launches=product_launches,
            context=context,
        )

        # Return in legacy format for backward compatibility
        schedule = []
        for entry in result.get("calendar", [])[:10]:
            schedule.append({
                "date": entry["date"],
                "channel": entry["channel"],
                "type": entry["content_type"],
                "status": entry["status"],
                "suggested_time": entry["time"],
                "notes": entry["description"],
                "event_name": entry.get("related_event"),
            })

        if not schedule:
            # Fallback: generate basic schedule
            now = datetime.now(timezone.utc)
            channels = ["LinkedIn", "Twitter", "Email", "Blog"]
            for i in range(4):
                post_date = now + timedelta(days=(i + 1) * 2)
                schedule.append({
                    "date": post_date.strftime("%Y-%m-%d"),
                    "channel": channels[i % len(channels)],
                    "type": "post",
                    "status": "planned",
                    "suggested_time": "10:00 UTC",
                    "notes": f"Content piece #{i + 1} - to be generated",
                })

        return {"schedule": schedule}

    # ── Brand Voice ─────────────────────────────────────────────────────

    async def learn_brand_voice(
        self,
        brand_name: str,
        samples: list[str],
    ) -> dict:
        """
        Analyse writing samples to build a brand voice profile.

        Args:
            brand_name: Name of the brand.
            samples: List of writing samples.

        Returns:
            Dict with the brand voice profile.
        """
        profile = await self.brand_voice.learn_voice(brand_name, samples)
        return {
            "profile": profile.to_dict(),
            "prompt_fragment": profile.to_prompt_fragment(),
            "message": f"Brand voice profile created for '{brand_name}'.",
        }

    async def check_brand_consistency(
        self,
        brand_name: str,
        copy_text: str,
    ) -> dict:
        """
        Check if copy is consistent with the brand voice.

        Args:
            brand_name: Brand to check against.
            copy_text: Copy to evaluate.

        Returns:
            Dict with scores and suggestions.
        """
        return await self.brand_voice.check_consistency(brand_name, copy_text)

    # ── Translation ─────────────────────────────────────────────────────

    async def translate_copy(
        self,
        copy_text: str,
        target_language: str,
        source_language: str = "en",
        formality: Optional[str] = None,
        context: Optional[dict] = None,
    ) -> dict:
        """
        Translate and culturally adapt marketing copy.

        Args:
            copy_text: Original copy.
            target_language: Target language code or name.
            source_language: Source language code.
            formality: Formality level override.
            context: Additional context.

        Returns:
            Dict with translated text and metadata.
        """
        return await self.multilingual.translate_copy(
            copy_text=copy_text,
            target_language=target_language,
            source_language=source_language,
            formality=formality,
        )

    async def batch_translate(
        self,
        copy_text: str,
        target_languages: list[str],
        source_language: str = "en",
    ) -> dict:
        """
        Translate copy into multiple languages.

        Args:
            copy_text: Original copy.
            target_languages: List of target language codes.
            source_language: Source language code.

        Returns:
            Dict with all translations.
        """
        return await self.multilingual.batch_translate(
            copy_text=copy_text,
            target_languages=target_languages,
            source_language=source_language,
        )

    # ── Capability Listings ─────────────────────────────────────────────

    def get_available_tones(self) -> list[str]:
        """Return all available tone preset names."""
        return list_tones()

    def get_available_formats(self) -> list[str]:
        """Return all available copy format names."""
        return list_formats()

    def get_available_languages(self) -> list[dict]:
        """Return all supported languages."""
        return list_languages()

    def get_brand_profiles(self) -> list[str]:
        """Return all stored brand voice profile names."""
        return self.brand_voice.list_profiles()

    # ── Internal Helpers ────────────────────────────────────────────────

    def _get_brand_guidelines(self, brand_name: Optional[str] = None) -> str:
        """Retrieve brand guidelines from voice profile or memory."""
        if brand_name:
            guidelines = self.brand_voice.get_guidelines_for_copy(brand_name)
            if "No specific" not in guidelines:
                return guidelines

        if self.memory:
            try:
                stored = self.memory.read_from_folder("knowledge_base/brand_guidelines.md")
                if stored:
                    return stored
            except Exception:
                pass

        return "No specific brand guidelines provided."

    async def _call_llm(self, prompt: str) -> str:
        """Call the LLM with a prompt."""
        if self.llm:
            try:
                messages = [
                    {"role": "system", "content": "You are a creative marketing expert and copywriter."},
                    {"role": "user", "content": prompt},
                ]
                return await self.llm.generate(messages)
            except Exception as e:
                return f"[Creative Error: {str(e)}]"
        return (
            "[Demo Mode] Creative content would be generated here. "
            "Configure OPENAI_API_KEY to enable full creative capabilities."
        )
