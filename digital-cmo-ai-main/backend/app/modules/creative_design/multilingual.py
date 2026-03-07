"""
Multi-Language Support for the Creative & Design Module.

Provides language-aware copy generation, translation, and
cultural adaptation for marketing content across supported languages.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class LanguageProfile:
    """Configuration for a supported language."""

    code: str  # ISO 639-1
    name: str
    native_name: str
    writing_direction: str = "ltr"
    formality_default: str = "formal"
    cultural_notes: str = ""
    date_format: str = "YYYY-MM-DD"
    currency_symbol: str = "$"
    common_greetings: list[str] = field(default_factory=list)
    marketing_tips: list[str] = field(default_factory=list)


# ── Supported Languages ─────────────────────────────────────────────────

ENGLISH = LanguageProfile(
    code="en",
    name="English",
    native_name="English",
    formality_default="neutral",
    cultural_notes="Direct communication style. Humour and wordplay are effective.",
    date_format="MM/DD/YYYY",
    currency_symbol="$",
    common_greetings=["Hi", "Hello", "Hey there"],
    marketing_tips=[
        "Use strong action verbs",
        "Keep sentences concise",
        "Leverage social proof",
        "Use numbers and statistics",
    ],
)

SPANISH = LanguageProfile(
    code="es",
    name="Spanish",
    native_name="Espanol",
    formality_default="formal",
    cultural_notes=(
        "Distinguish between 'tu' (informal) and 'usted' (formal). "
        "Emotional and relationship-oriented messaging resonates well. "
        "Be aware of regional variations (Spain vs. Latin America)."
    ),
    date_format="DD/MM/YYYY",
    currency_symbol="EUR/USD",
    common_greetings=["Hola", "Buenos dias", "Que tal"],
    marketing_tips=[
        "Use warm, personal language",
        "Emphasise community and family values",
        "Adapt for regional Spanish variants",
        "Use exclamation marks at both ends for emphasis",
    ],
)

FRENCH = LanguageProfile(
    code="fr",
    name="French",
    native_name="Francais",
    formality_default="formal",
    cultural_notes=(
        "French marketing tends to be more elegant and sophisticated. "
        "Use 'vous' for formal contexts, 'tu' for casual brands. "
        "Avoid direct translations of English idioms."
    ),
    date_format="DD/MM/YYYY",
    currency_symbol="EUR",
    common_greetings=["Bonjour", "Salut", "Bonsoir"],
    marketing_tips=[
        "Maintain elegance and sophistication",
        "Use formal register unless targeting youth",
        "Respect French language purity (avoid anglicisms where possible)",
        "Emphasise quality and craftsmanship",
    ],
)

GERMAN = LanguageProfile(
    code="de",
    name="German",
    native_name="Deutsch",
    formality_default="formal",
    cultural_notes=(
        "German audiences value precision, reliability, and thoroughness. "
        "Use 'Sie' for formal, 'du' for informal. "
        "Data-driven claims are more persuasive than emotional appeals."
    ),
    date_format="DD.MM.YYYY",
    currency_symbol="EUR",
    common_greetings=["Hallo", "Guten Tag", "Servus"],
    marketing_tips=[
        "Be precise and factual",
        "Include technical specifications",
        "Use formal address unless brand is explicitly casual",
        "Emphasise quality, engineering, and reliability",
    ],
)

PORTUGUESE = LanguageProfile(
    code="pt",
    name="Portuguese",
    native_name="Portugues",
    formality_default="neutral",
    cultural_notes=(
        "Distinguish between European Portuguese and Brazilian Portuguese. "
        "Brazilian Portuguese is warmer and more informal. "
        "Emotional storytelling works well in both variants."
    ),
    date_format="DD/MM/YYYY",
    currency_symbol="EUR/BRL",
    common_greetings=["Ola", "Bom dia", "E ai"],
    marketing_tips=[
        "Use storytelling and emotional appeals",
        "Adapt for Brazilian vs. European Portuguese",
        "Emphasise personal connections",
        "Use inclusive and warm language",
    ],
)


# ── Registry ────────────────────────────────────────────────────────────

LANGUAGE_REGISTRY: dict[str, LanguageProfile] = {
    "en": ENGLISH,
    "english": ENGLISH,
    "es": SPANISH,
    "spanish": SPANISH,
    "fr": FRENCH,
    "french": FRENCH,
    "de": GERMAN,
    "german": GERMAN,
    "pt": PORTUGUESE,
    "portuguese": PORTUGUESE,
}


def get_language(code_or_name: str) -> LanguageProfile:
    """Return a language profile by code or name, falling back to English."""
    return LANGUAGE_REGISTRY.get(code_or_name.lower(), ENGLISH)


def list_languages() -> list[dict]:
    """Return all supported languages with their codes and names."""
    seen = set()
    result = []
    for profile in LANGUAGE_REGISTRY.values():
        if profile.code not in seen:
            seen.add(profile.code)
            result.append({
                "code": profile.code,
                "name": profile.name,
                "native_name": profile.native_name,
            })
    return result


# ── Translation & Adaptation Prompts ────────────────────────────────────

TRANSLATION_PROMPT = """You are a professional marketing translator and cultural adaptation specialist.

Translate and culturally adapt the following marketing copy from {source_language} to {target_language}.

ORIGINAL COPY ({source_language}):
{copy_text}

TARGET LANGUAGE: {target_language} ({target_native_name})

CULTURAL NOTES FOR {target_language}:
{cultural_notes}

MARKETING TIPS FOR {target_language}:
{marketing_tips}

FORMALITY LEVEL: {formality}

INSTRUCTIONS:
- Do NOT produce a literal word-for-word translation
- Adapt idioms, metaphors, and cultural references for the target market
- Maintain the same persuasive intent and emotional impact
- Adjust formality level as specified
- Keep brand names and product names unchanged
- Adapt date formats, currency symbols, and number formats as needed
- If the copy contains hashtags, adapt them for the target language/market

Provide ONLY the translated and adapted copy, nothing else.
"""

MULTILINGUAL_GENERATION_PROMPT = """Write marketing copy in {target_language} ({target_native_name}).

Brief: {brief}
{tone_fragment}
Target length: ~{length} words
Brand guidelines: {guidelines}

CULTURAL CONTEXT FOR {target_language}:
{cultural_notes}

MARKETING BEST PRACTICES FOR {target_language}:
{marketing_tips}

FORMALITY LEVEL: {formality}

Write the copy directly in {target_language}. Do NOT write in English first.
Ensure the copy feels native and natural to {target_language} speakers.
"""


class MultilingualEngine:
    """
    Handles multi-language copy generation and translation.
    """

    def __init__(self, llm_client=None):
        self.llm = llm_client

    async def translate_copy(
        self,
        copy_text: str,
        target_language: str,
        source_language: str = "en",
        formality: Optional[str] = None,
    ) -> dict:
        """
        Translate and culturally adapt marketing copy.

        Args:
            copy_text: Original copy text.
            target_language: Target language code or name.
            source_language: Source language code or name.
            formality: Override formality level.

        Returns:
            Dict with translated text and metadata.
        """
        source_profile = get_language(source_language)
        target_profile = get_language(target_language)
        formality = formality or target_profile.formality_default

        prompt = TRANSLATION_PROMPT.format(
            source_language=source_profile.name,
            target_language=target_profile.name,
            target_native_name=target_profile.native_name,
            copy_text=copy_text,
            cultural_notes=target_profile.cultural_notes,
            marketing_tips="\n".join(f"- {t}" for t in target_profile.marketing_tips),
            formality=formality,
        )

        translated = await self._call_llm(prompt)

        return {
            "original": copy_text,
            "translated": translated,
            "source_language": source_profile.code,
            "target_language": target_profile.code,
            "formality": formality,
        }

    async def generate_multilingual(
        self,
        brief: str,
        target_language: str,
        tone_fragment: str = "",
        length: int = 200,
        guidelines: str = "",
        formality: Optional[str] = None,
    ) -> dict:
        """
        Generate copy directly in the target language.

        Args:
            brief: Content brief.
            target_language: Language code or name.
            tone_fragment: Tone preset prompt fragment.
            length: Approximate word count.
            guidelines: Brand guidelines.
            formality: Override formality level.

        Returns:
            Dict with generated copy and metadata.
        """
        profile = get_language(target_language)
        formality = formality or profile.formality_default

        prompt = MULTILINGUAL_GENERATION_PROMPT.format(
            target_language=profile.name,
            target_native_name=profile.native_name,
            brief=brief,
            tone_fragment=tone_fragment,
            length=length,
            guidelines=guidelines or "No specific guidelines.",
            cultural_notes=profile.cultural_notes,
            marketing_tips="\n".join(f"- {t}" for t in profile.marketing_tips),
            formality=formality,
        )

        content = await self._call_llm(prompt)

        return {
            "content": content,
            "language": profile.code,
            "language_name": profile.name,
            "formality": formality,
        }

    async def batch_translate(
        self,
        copy_text: str,
        target_languages: list[str],
        source_language: str = "en",
    ) -> dict:
        """
        Translate copy into multiple languages at once.

        Args:
            copy_text: Original copy.
            target_languages: List of target language codes/names.
            source_language: Source language code.

        Returns:
            Dict mapping language codes to translated text.
        """
        results = {}
        for lang in target_languages:
            result = await self.translate_copy(
                copy_text=copy_text,
                target_language=lang,
                source_language=source_language,
            )
            results[result["target_language"]] = result

        return {
            "original": copy_text,
            "source_language": source_language,
            "translations": results,
            "languages_count": len(results),
        }

    async def _call_llm(self, prompt: str) -> str:
        """Call the LLM."""
        if self.llm:
            try:
                messages = [
                    {"role": "system", "content": "You are a professional multilingual marketing copywriter and translator."},
                    {"role": "user", "content": prompt},
                ]
                return await self.llm.generate(messages)
            except Exception as e:
                return f"[Translation Error: {str(e)}]"
        return "[Demo Mode] Multilingual content would be generated here."
