"""
Comprehensive Unit Tests for the Creative & Design Module.

Covers:
- Copy generation across all 11 formats
- Tone presets (6 built-in + custom)
- A/B testing engine with variant generation and scoring
- Smart content calendar with events, channels, and optimal times
- Brand voice learning and consistency checking
- Multi-language support and translation
- Image prompt generation
- Legacy backward compatibility
- Handler routing
"""

import json
from datetime import datetime, timedelta, timezone

import pytest

from app.modules.creative_design import (
    CreativeDesignModule,
    ABTestingEngine,
    ABVariant,
    ContentCalendarEngine,
    CalendarEntry,
    BrandVoiceLearner,
    BrandVoiceProfile,
    MultilingualEngine,
)
from app.modules.creative_design.tone_presets import (
    TonePreset,
    get_tone,
    list_tones,
    register_custom_tone,
    TONE_REGISTRY,
    PROFESSIONAL,
    PLAYFUL,
    URGENT,
    EMPATHETIC,
    AUTHORITATIVE,
    CONVERSATIONAL,
)
from app.modules.creative_design.copy_formats import (
    CopyFormat,
    get_format,
    list_formats,
    FORMAT_REGISTRY,
)
from app.modules.creative_design.content_calendar import (
    OPTIMAL_POSTING_TIMES,
    SEASONAL_EVENTS,
    INDUSTRY_EVENTS,
    CONTENT_MIX,
)
from app.modules.creative_design.multilingual import (
    get_language,
    list_languages,
    LANGUAGE_REGISTRY,
)


# ════════════════════════════════════════════════════════════════════════
# Fixtures
# ════════════════════════════════════════════════════════════════════════

@pytest.fixture
def module():
    """Provide a CreativeDesignModule in demo mode (no LLM)."""
    return CreativeDesignModule()


@pytest.fixture
def ab_engine():
    """Provide an ABTestingEngine in demo mode."""
    return ABTestingEngine()


@pytest.fixture
def calendar_engine():
    """Provide a ContentCalendarEngine in demo mode."""
    return ContentCalendarEngine()


@pytest.fixture
def brand_learner():
    """Provide a BrandVoiceLearner in demo mode."""
    return BrandVoiceLearner()


@pytest.fixture
def multilingual_engine():
    """Provide a MultilingualEngine in demo mode."""
    return MultilingualEngine()


# ════════════════════════════════════════════════════════════════════════
# Tone Presets
# ════════════════════════════════════════════════════════════════════════

class TestTonePresets:
    """Tests for tone preset definitions and registry."""

    def test_all_six_builtin_tones_exist(self):
        tones = list_tones()
        assert len(tones) >= 6
        for name in ["professional", "playful", "urgent", "empathetic", "authoritative", "conversational"]:
            assert name in tones

    def test_get_tone_returns_correct_preset(self):
        tone = get_tone("playful")
        assert tone.name == "playful"
        assert tone.emoji_allowed is True

    def test_get_tone_fallback_to_professional(self):
        tone = get_tone("nonexistent_tone")
        assert tone.name == "professional"

    def test_tone_prompt_fragment_contains_key_info(self):
        fragment = PROFESSIONAL.to_prompt_fragment()
        assert "professional" in fragment.lower()
        assert "Tone:" in fragment
        assert "Writing instructions:" in fragment

    def test_tone_preset_is_frozen(self):
        with pytest.raises(AttributeError):
            PROFESSIONAL.name = "modified"

    def test_register_custom_tone(self):
        custom = TonePreset(
            name="sarcastic",
            description="Witty and sarcastic.",
            system_instruction="Write with dry wit and sarcasm.",
            vocabulary_hints=["obviously", "clearly", "shocking"],
            emoji_allowed=False,
        )
        register_custom_tone(custom)
        assert "sarcastic" in list_tones()
        retrieved = get_tone("sarcastic")
        assert retrieved.name == "sarcastic"
        # Clean up
        del TONE_REGISTRY["sarcastic"]

    def test_professional_no_exclamation(self):
        assert PROFESSIONAL.max_exclamation_marks == 0

    def test_playful_allows_emoji(self):
        assert PLAYFUL.emoji_allowed is True

    def test_urgent_vocabulary_hints(self):
        assert "now" in URGENT.vocabulary_hints
        assert "limited" in URGENT.vocabulary_hints

    def test_empathetic_description(self):
        assert "warm" in EMPATHETIC.description.lower()

    def test_authoritative_sentence_style(self):
        assert "evidence" in AUTHORITATIVE.sentence_style.lower()

    def test_conversational_hints(self):
        assert "hey" in CONVERSATIONAL.vocabulary_hints


# ════════════════════════════════════════════════════════════════════════
# Copy Formats
# ════════════════════════════════════════════════════════════════════════

class TestCopyFormats:
    """Tests for copy format definitions and registry."""

    def test_all_eleven_formats_exist(self):
        formats = list_formats()
        expected = [
            "blog_post", "social_caption", "email_subject", "ad_headline",
            "product_description", "linkedin_post", "twitter_thread",
            "youtube_script", "press_release", "landing_page", "sms_campaign",
        ]
        for name in expected:
            assert name in formats, f"Missing format: {name}"

    def test_get_format_returns_correct_format(self):
        fmt = get_format("linkedin_post")
        assert fmt.name == "linkedin_post"
        assert fmt.platform == "linkedin"

    def test_get_format_fallback_to_blog_post(self):
        fmt = get_format("nonexistent_format")
        assert fmt.name == "blog_post"

    def test_format_build_prompt(self):
        fmt = get_format("blog_post")
        prompt = fmt.build_prompt(
            brief="Write about AI in marketing",
            tone_fragment="Tone: professional",
            guidelines="Keep it under 1000 words",
            language="English",
        )
        assert "AI in marketing" in prompt
        assert "professional" in prompt
        assert "English" in prompt

    def test_sms_campaign_short_length(self):
        fmt = get_format("sms_campaign")
        assert fmt.default_length <= 50
        assert fmt.max_length <= 50

    def test_youtube_script_long_length(self):
        fmt = get_format("youtube_script")
        assert fmt.default_length >= 500

    def test_press_release_structural_hints(self):
        fmt = get_format("press_release")
        hints_text = " ".join(fmt.structural_hints).lower()
        assert "dateline" in hints_text
        assert "headline" in hints_text

    def test_landing_page_has_cta_hint(self):
        fmt = get_format("landing_page")
        hints_text = " ".join(fmt.structural_hints).lower()
        assert "cta" in hints_text

    def test_twitter_thread_character_limit(self):
        fmt = get_format("twitter_thread")
        hints_text = " ".join(fmt.structural_hints).lower()
        assert "280" in hints_text

    def test_email_subject_spam_avoidance(self):
        fmt = get_format("email_subject")
        hints_text = " ".join(fmt.structural_hints).lower()
        assert "spam" in hints_text

    def test_all_formats_have_prompt_template(self):
        for name in list_formats():
            fmt = get_format(name)
            assert fmt.prompt_template, f"Format {name} has no prompt template"
            assert "{brief}" in fmt.prompt_template


# ════════════════════════════════════════════════════════════════════════
# Copy Generation (Module Level)
# ════════════════════════════════════════════════════════════════════════

class TestCopyGeneration:
    """Tests for the main copy generation pipeline."""

    @pytest.mark.asyncio
    async def test_generate_copy_default(self, module):
        result = await module.generate_copy("Write about AI in marketing")
        assert "content" in result
        assert result["content"] != ""
        assert "metadata" in result
        assert result["metadata"]["tone"] == "professional"
        assert result["metadata"]["format"] == "blog_post"

    @pytest.mark.asyncio
    async def test_generate_copy_with_tone(self, module):
        result = await module.generate_copy("Product launch email", tone="urgent")
        assert result["metadata"]["tone"] == "urgent"

    @pytest.mark.asyncio
    async def test_generate_copy_with_format(self, module):
        result = await module.generate_copy(
            "New SaaS product", copy_format="linkedin_post"
        )
        assert result["metadata"]["format"] == "linkedin_post"

    @pytest.mark.asyncio
    async def test_generate_copy_with_language(self, module):
        result = await module.generate_copy(
            "Write about AI", language="es"
        )
        assert result["metadata"]["language"] == "es"

    @pytest.mark.asyncio
    async def test_generate_copy_returns_alternatives_list(self, module):
        result = await module.generate_copy("Test brief")
        assert isinstance(result["alternatives"], list)

    @pytest.mark.asyncio
    async def test_generate_copy_all_formats(self, module):
        for fmt_name in list_formats():
            result = await module.generate_copy(
                f"Test brief for {fmt_name}", copy_format=fmt_name
            )
            assert "content" in result
            assert result["metadata"]["format"] == fmt_name

    @pytest.mark.asyncio
    async def test_generate_copy_all_tones(self, module):
        for tone_name in list_tones():
            result = await module.generate_copy(
                f"Test brief with {tone_name} tone", tone=tone_name
            )
            assert result["metadata"]["tone"] == tone_name


# ════════════════════════════════════════════════════════════════════════
# Image Generation
# ════════════════════════════════════════════════════════════════════════

class TestImageGeneration:
    """Tests for image prompt generation."""

    @pytest.mark.asyncio
    async def test_generate_image_no_api(self, module):
        result = await module.generate_image("Modern tech banner")
        assert "content" in result
        assert result.get("image_url") is None

    @pytest.mark.asyncio
    async def test_generate_image_with_style(self, module):
        result = await module.generate_image(
            "Product showcase", style="minimalist"
        )
        assert "content" in result

    @pytest.mark.asyncio
    async def test_generate_image_with_brand(self, module):
        result = await module.generate_image(
            "Banner for campaign", brand_name="TestBrand"
        )
        assert "content" in result


# ════════════════════════════════════════════════════════════════════════
# A/B Testing Engine
# ════════════════════════════════════════════════════════════════════════

class TestABTestingEngine:
    """Tests for the A/B testing engine."""

    @pytest.mark.asyncio
    async def test_generate_variants_returns_list(self, ab_engine):
        variants = await ab_engine.generate_variants("Buy now and save 20%!")
        assert isinstance(variants, list)
        assert len(variants) >= 3

    @pytest.mark.asyncio
    async def test_generate_variants_respects_count(self, ab_engine):
        variants = await ab_engine.generate_variants("Test copy", num_variants=3)
        assert len(variants) >= 3

    @pytest.mark.asyncio
    async def test_generate_variants_max_five(self, ab_engine):
        variants = await ab_engine.generate_variants("Test copy", num_variants=10)
        assert len(variants) <= 5

    @pytest.mark.asyncio
    async def test_generate_variants_min_three(self, ab_engine):
        variants = await ab_engine.generate_variants("Test copy", num_variants=1)
        assert len(variants) >= 3

    @pytest.mark.asyncio
    async def test_variant_has_required_fields(self, ab_engine):
        variants = await ab_engine.generate_variants("Test copy")
        for v in variants:
            assert hasattr(v, "variant_id")
            assert hasattr(v, "label")
            assert hasattr(v, "copy_text")
            assert hasattr(v, "strategy")

    @pytest.mark.asyncio
    async def test_score_variant(self, ab_engine):
        variant = ABVariant(
            variant_id="test",
            label="Test Variant",
            copy_text="Buy now and save 20%!",
            strategy="Test strategy",
            tone_used="urgent",
        )
        scored = await ab_engine.score_variant(variant)
        assert scored.overall_score >= 0
        assert isinstance(scored.dimension_scores, dict)

    @pytest.mark.asyncio
    async def test_generate_and_score_full_pipeline(self, ab_engine):
        result = await ab_engine.generate_and_score("Buy now and save 20%!")
        assert "base_copy" in result
        assert "variants" in result
        assert "recommended_variant" in result
        assert "summary" in result
        assert result["num_variants"] >= 3

    @pytest.mark.asyncio
    async def test_generate_and_score_variants_sorted(self, ab_engine):
        result = await ab_engine.generate_and_score("Test copy")
        variants = result["variants"]
        if len(variants) >= 2:
            scores = [v["overall_score"] for v in variants]
            assert scores == sorted(scores, reverse=True)

    def test_variant_to_dict(self):
        variant = ABVariant(
            variant_id="test",
            label="Test",
            copy_text="Test copy",
            strategy="Test",
            tone_used="professional",
            overall_score=85.5,
            predicted_ctr_lift=12.3,
        )
        d = variant.to_dict()
        assert d["variant_id"] == "test"
        assert d["overall_score"] == 85.5
        assert d["predicted_ctr_lift"] == "+12.3%"

    def test_extract_json_with_fences(self):
        text = '```json\n[{"key": "value"}]\n```'
        result = ABTestingEngine._extract_json(text)
        assert json.loads(result) == [{"key": "value"}]

    def test_extract_json_plain(self):
        text = '{"key": "value"}'
        result = ABTestingEngine._extract_json(text)
        assert json.loads(result) == {"key": "value"}

    def test_build_summary(self):
        variants = [
            ABVariant("a", "A", "copy a", "s", "t", overall_score=90, predicted_ctr_lift=15),
            ABVariant("b", "B", "copy b", "s", "t", overall_score=70, predicted_ctr_lift=5),
        ]
        summary = ABTestingEngine._build_summary(variants)
        assert "2 variants" in summary
        assert "90.0" in summary


# ════════════════════════════════════════════════════════════════════════
# A/B Testing via Module
# ════════════════════════════════════════════════════════════════════════

class TestABTestingModule:
    """Tests for A/B testing through the main module."""

    @pytest.mark.asyncio
    async def test_suggest_ab_tests(self, module):
        result = await module.suggest_ab_tests("Buy now and save 20%!")
        assert "variants" in result
        assert "base_copy" in result
        assert result["base_copy"] == "Buy now and save 20%!"

    @pytest.mark.asyncio
    async def test_suggest_ab_tests_with_num_variants(self, module):
        result = await module.suggest_ab_tests("Test copy", num_variants=5)
        assert result["num_variants"] <= 5


# ════════════════════════════════════════════════════════════════════════
# Content Calendar
# ════════════════════════════════════════════════════════════════════════

class TestContentCalendar:
    """Tests for the smart content calendar engine."""

    @pytest.mark.asyncio
    async def test_generate_calendar_default(self, calendar_engine):
        result = await calendar_engine.generate_calendar()
        assert "calendar" in result
        assert "date_range" in result
        assert "channels" in result
        assert result["total_entries"] > 0

    @pytest.mark.asyncio
    async def test_generate_calendar_with_dates(self, calendar_engine):
        result = await calendar_engine.generate_calendar(
            start_date="2026-04-01",
            end_date="2026-04-15",
        )
        assert result["date_range"]["start"] == "2026-04-01"
        assert result["date_range"]["end"] == "2026-04-15"
        assert result["date_range"]["total_days"] == 14

    @pytest.mark.asyncio
    async def test_generate_calendar_with_channels(self, calendar_engine):
        result = await calendar_engine.generate_calendar(
            channels=["linkedin", "email"],
            start_date="2026-04-01",
            end_date="2026-04-10",
        )
        assert set(result["channels"]) == {"linkedin", "email"}
        for entry in result["calendar"]:
            assert entry["channel"] in ["linkedin", "email"]

    @pytest.mark.asyncio
    async def test_generate_calendar_with_industry(self, calendar_engine):
        result = await calendar_engine.generate_calendar(
            industry="technology",
            start_date="2026-01-01",
            end_date="2026-01-31",
        )
        # Should include CES event
        event_names = [e["name"] for e in result["events_included"]]
        assert any("CES" in name for name in event_names)

    @pytest.mark.asyncio
    async def test_generate_calendar_with_product_launch(self, calendar_engine):
        result = await calendar_engine.generate_calendar(
            start_date="2026-04-01",
            end_date="2026-04-30",
            product_launches=[{
                "name": "Product X Launch",
                "date": "2026-04-15",
                "description": "Major product launch",
            }],
        )
        event_names = [e["name"] for e in result["events_included"]]
        assert "Product X Launch" in event_names

    @pytest.mark.asyncio
    async def test_generate_calendar_with_custom_events(self, calendar_engine):
        result = await calendar_engine.generate_calendar(
            start_date="2026-05-01",
            end_date="2026-05-31",
            custom_events=[{
                "name": "Company Anniversary",
                "date": "2026-05-15",
                "type": "custom",
            }],
        )
        event_names = [e["name"] for e in result["events_included"]]
        assert "Company Anniversary" in event_names

    @pytest.mark.asyncio
    async def test_calendar_entries_have_required_fields(self, calendar_engine):
        result = await calendar_engine.generate_calendar(
            start_date="2026-04-01",
            end_date="2026-04-07",
        )
        for entry in result["calendar"]:
            assert "date" in entry
            assert "channel" in entry
            assert "content_type" in entry
            assert "status" in entry
            assert "time" in entry

    @pytest.mark.asyncio
    async def test_calendar_content_mix_present(self, calendar_engine):
        result = await calendar_engine.generate_calendar()
        assert "content_mix" in result
        assert "educational" in result["content_mix"]

    @pytest.mark.asyncio
    async def test_calendar_posting_guidelines_present(self, calendar_engine):
        result = await calendar_engine.generate_calendar(channels=["linkedin"])
        assert "posting_guidelines" in result
        assert "linkedin" in result["posting_guidelines"]

    def test_optimal_posting_times_structure(self):
        for channel, info in OPTIMAL_POSTING_TIMES.items():
            assert "best_days" in info
            assert "best_hours" in info
            assert "frequency" in info

    def test_seasonal_events_coverage(self):
        months_covered = {e["month"] for e in SEASONAL_EVENTS}
        # Should cover at least 8 months
        assert len(months_covered) >= 8

    def test_industry_events_keys(self):
        expected_industries = ["technology", "marketing", "finance", "ecommerce", "healthcare"]
        for industry in expected_industries:
            assert industry in INDUSTRY_EVENTS

    def test_content_mix_ratios_sum_to_one(self):
        total = sum(v["ratio"] for v in CONTENT_MIX.values())
        assert abs(total - 1.0) < 0.01

    def test_get_optimal_times(self, calendar_engine):
        times = calendar_engine.get_optimal_times("linkedin")
        assert "best_days" in times
        assert "Tuesday" in times["best_days"]

    def test_get_seasonal_events_by_month(self, calendar_engine):
        december_events = calendar_engine.get_seasonal_events(month=12)
        assert len(december_events) >= 2

    def test_get_industry_events(self, calendar_engine):
        tech_events = calendar_engine.get_industry_events("technology")
        assert len(tech_events) >= 3

    def test_calendar_entry_to_dict(self):
        entry = CalendarEntry(
            date="2026-04-01",
            day_of_week="Wednesday",
            time="10:00",
            channel="linkedin",
            content_type="post",
            content_category="educational",
            title="Test Post",
            description="Test description",
        )
        d = entry.to_dict()
        assert d["date"] == "2026-04-01"
        assert d["channel"] == "linkedin"


# ════════════════════════════════════════════════════════════════════════
# Content Calendar via Module
# ════════════════════════════════════════════════════════════════════════

class TestContentCalendarModule:
    """Tests for content calendar through the main module."""

    @pytest.mark.asyncio
    async def test_create_content_calendar(self, module):
        result = await module.create_content_calendar()
        assert "calendar" in result
        assert result["total_entries"] > 0

    @pytest.mark.asyncio
    async def test_create_content_schedule_legacy(self, module):
        result = await module.create_content_schedule([])
        assert "schedule" in result
        assert len(result["schedule"]) > 0

    @pytest.mark.asyncio
    async def test_create_content_schedule_with_events(self, module):
        events = [
            {"name": "Product Launch", "date": "2026-04-01", "channel": "email"},
            {"name": "Webinar", "date": "2026-04-15", "channel": "LinkedIn"},
        ]
        result = await module.create_content_schedule(events)
        assert "schedule" in result
        assert len(result["schedule"]) > 0


# ════════════════════════════════════════════════════════════════════════
# Brand Voice Learning
# ════════════════════════════════════════════════════════════════════════

class TestBrandVoiceLearner:
    """Tests for the brand voice learning system."""

    @pytest.mark.asyncio
    async def test_learn_voice(self, brand_learner):
        samples = [
            "We empower teams to build faster with our cutting-edge platform.",
            "Transform your workflow with seamless integrations and real-time analytics.",
            "Built for teams that move fast. See the difference in days, not months.",
        ]
        profile = await brand_learner.learn_voice("TestBrand", samples)
        assert isinstance(profile, BrandVoiceProfile)
        assert profile.brand_name == "TestBrand"
        assert len(profile.tone_attributes) > 0

    @pytest.mark.asyncio
    async def test_get_profile_after_learning(self, brand_learner):
        samples = ["Test sample content for brand voice analysis."]
        await brand_learner.learn_voice("MyBrand", samples)
        profile = brand_learner.get_profile("MyBrand")
        assert profile is not None
        assert profile.brand_name == "MyBrand"

    @pytest.mark.asyncio
    async def test_get_profile_nonexistent(self, brand_learner):
        profile = brand_learner.get_profile("NonexistentBrand")
        assert profile is None

    @pytest.mark.asyncio
    async def test_list_profiles(self, brand_learner):
        samples = ["Sample content."]
        await brand_learner.learn_voice("Brand1", samples)
        await brand_learner.learn_voice("Brand2", samples)
        profiles = brand_learner.list_profiles()
        assert "brand1" in profiles
        assert "brand2" in profiles

    @pytest.mark.asyncio
    async def test_check_consistency_no_profile(self, brand_learner):
        result = await brand_learner.check_consistency("Unknown", "Test copy")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_check_consistency_with_profile(self, brand_learner):
        samples = ["Professional and innovative content."]
        await brand_learner.learn_voice("CheckBrand", samples)
        result = await brand_learner.check_consistency(
            "CheckBrand", "Test copy to check"
        )
        assert "scores" in result

    def test_brand_voice_profile_to_dict(self):
        profile = BrandVoiceProfile(
            brand_name="Test",
            tone_attributes=["professional", "warm"],
            values=["innovation"],
        )
        d = profile.to_dict()
        assert d["brand_name"] == "Test"
        assert "professional" in d["tone_attributes"]

    def test_brand_voice_profile_from_dict(self):
        data = {
            "brand_name": "Test",
            "tone_attributes": ["professional"],
            "vocabulary_preferences": ["empower"],
            "values": ["innovation"],
        }
        profile = BrandVoiceProfile.from_dict(data)
        assert profile.brand_name == "Test"
        assert "empower" in profile.vocabulary_preferences

    def test_brand_voice_profile_to_prompt_fragment(self):
        profile = BrandVoiceProfile(
            brand_name="Test",
            tone_attributes=["professional", "warm"],
            vocabulary_preferences=["empower", "transform"],
            dos=["Use active voice"],
            donts=["Use jargon"],
        )
        fragment = profile.to_prompt_fragment()
        assert "Test" in fragment
        assert "professional" in fragment
        assert "empower" in fragment

    def test_get_guidelines_for_copy_no_profile(self, brand_learner):
        guidelines = brand_learner.get_guidelines_for_copy("Unknown")
        assert "No specific" in guidelines


# ════════════════════════════════════════════════════════════════════════
# Brand Voice via Module
# ════════════════════════════════════════════════════════════════════════

class TestBrandVoiceModule:
    """Tests for brand voice through the main module."""

    @pytest.mark.asyncio
    async def test_learn_brand_voice(self, module):
        result = await module.learn_brand_voice(
            "ModuleBrand",
            ["Sample marketing content for analysis."],
        )
        assert "profile" in result
        assert "message" in result
        assert "ModuleBrand" in result["message"]

    @pytest.mark.asyncio
    async def test_check_brand_consistency(self, module):
        await module.learn_brand_voice("ConsistBrand", ["Professional content."])
        result = await module.check_brand_consistency(
            "ConsistBrand", "Test copy to evaluate."
        )
        assert "scores" in result

    def test_get_brand_profiles(self, module):
        profiles = module.get_brand_profiles()
        assert isinstance(profiles, list)


# ════════════════════════════════════════════════════════════════════════
# Multi-Language Support
# ════════════════════════════════════════════════════════════════════════

class TestMultilingualEngine:
    """Tests for multi-language support."""

    def test_all_five_languages_exist(self):
        languages = list_languages()
        codes = {lang["code"] for lang in languages}
        assert {"en", "es", "fr", "de", "pt"}.issubset(codes)

    def test_get_language_by_code(self):
        lang = get_language("es")
        assert lang.code == "es"
        assert lang.name == "Spanish"

    def test_get_language_by_name(self):
        lang = get_language("french")
        assert lang.code == "fr"

    def test_get_language_fallback_to_english(self):
        lang = get_language("klingon")
        assert lang.code == "en"

    def test_language_profile_has_cultural_notes(self):
        for code in ["en", "es", "fr", "de", "pt"]:
            lang = get_language(code)
            assert lang.cultural_notes != ""
            assert len(lang.marketing_tips) > 0

    def test_language_profile_has_greetings(self):
        for code in ["en", "es", "fr", "de", "pt"]:
            lang = get_language(code)
            assert len(lang.common_greetings) > 0

    @pytest.mark.asyncio
    async def test_translate_copy(self, multilingual_engine):
        result = await multilingual_engine.translate_copy(
            copy_text="Buy now and save 20%!",
            target_language="es",
        )
        assert "original" in result
        assert "translated" in result
        assert result["source_language"] == "en"
        assert result["target_language"] == "es"

    @pytest.mark.asyncio
    async def test_generate_multilingual(self, multilingual_engine):
        result = await multilingual_engine.generate_multilingual(
            brief="Write about AI in marketing",
            target_language="fr",
        )
        assert "content" in result
        assert result["language"] == "fr"

    @pytest.mark.asyncio
    async def test_batch_translate(self, multilingual_engine):
        result = await multilingual_engine.batch_translate(
            copy_text="Hello world",
            target_languages=["es", "fr", "de"],
        )
        assert "translations" in result
        assert result["languages_count"] == 3

    @pytest.mark.asyncio
    async def test_translate_with_formality(self, multilingual_engine):
        result = await multilingual_engine.translate_copy(
            copy_text="Check this out!",
            target_language="de",
            formality="formal",
        )
        assert result["formality"] == "formal"


# ════════════════════════════════════════════════════════════════════════
# Translation via Module
# ════════════════════════════════════════════════════════════════════════

class TestTranslationModule:
    """Tests for translation through the main module."""

    @pytest.mark.asyncio
    async def test_translate_copy(self, module):
        result = await module.translate_copy(
            copy_text="Test marketing copy",
            target_language="es",
        )
        assert "translated" in result

    @pytest.mark.asyncio
    async def test_batch_translate(self, module):
        result = await module.batch_translate(
            copy_text="Test copy",
            target_languages=["es", "fr"],
        )
        assert result["languages_count"] == 2


# ════════════════════════════════════════════════════════════════════════
# Handler Routing
# ════════════════════════════════════════════════════════════════════════

class TestHandlerRouting:
    """Tests for the generic handler's intent routing."""

    @pytest.mark.asyncio
    async def test_handle_copy_default(self, module):
        result = await module.handle("Write a blog post about marketing", {})
        assert "response" in result
        assert result["response"] != ""

    @pytest.mark.asyncio
    async def test_handle_image_routing(self, module):
        result = await module.handle("Generate a banner image for our campaign", {})
        assert "response" in result

    @pytest.mark.asyncio
    async def test_handle_ab_test_routing(self, module):
        result = await module.handle("Create an A/B test for this headline", {})
        assert "response" in result

    @pytest.mark.asyncio
    async def test_handle_calendar_routing(self, module):
        result = await module.handle("Create a content calendar for Q2", {})
        assert "response" in result

    @pytest.mark.asyncio
    async def test_handle_brand_voice_routing(self, module):
        result = await module.handle("Analyse our brand voice", {})
        assert "response" in result

    @pytest.mark.asyncio
    async def test_handle_translation_routing(self, module):
        result = await module.handle("Translate this to Spanish", {})
        assert "response" in result

    @pytest.mark.asyncio
    async def test_handle_visual_keyword(self, module):
        result = await module.handle("Create a visual for social media", {})
        assert "response" in result

    @pytest.mark.asyncio
    async def test_handle_variant_keyword(self, module):
        result = await module.handle("Generate variant options for this copy", {})
        assert "response" in result

    @pytest.mark.asyncio
    async def test_handle_schedule_keyword(self, module):
        result = await module.handle("Plan our content schedule", {})
        assert "response" in result


# ════════════════════════════════════════════════════════════════════════
# Capability Listings
# ════════════════════════════════════════════════════════════════════════

class TestCapabilities:
    """Tests for capability listing methods."""

    def test_get_available_tones(self, module):
        tones = module.get_available_tones()
        assert isinstance(tones, list)
        assert len(tones) >= 6

    def test_get_available_formats(self, module):
        formats = module.get_available_formats()
        assert isinstance(formats, list)
        assert len(formats) >= 11

    def test_get_available_languages(self, module):
        languages = module.get_available_languages()
        assert isinstance(languages, list)
        assert len(languages) >= 5

    def test_get_brand_profiles_empty(self, module):
        profiles = module.get_brand_profiles()
        assert isinstance(profiles, list)


# ════════════════════════════════════════════════════════════════════════
# Edge Cases & Error Handling
# ════════════════════════════════════════════════════════════════════════

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_generate_copy_empty_brief(self, module):
        result = await module.generate_copy("")
        assert "content" in result

    @pytest.mark.asyncio
    async def test_generate_copy_very_long_brief(self, module):
        long_brief = "Write about AI " * 500
        result = await module.generate_copy(long_brief)
        assert "content" in result

    @pytest.mark.asyncio
    async def test_generate_copy_special_characters(self, module):
        result = await module.generate_copy("Write about <script>alert('xss')</script>")
        assert "content" in result

    @pytest.mark.asyncio
    async def test_ab_test_empty_copy(self, ab_engine):
        result = await ab_engine.generate_and_score("")
        assert "variants" in result

    @pytest.mark.asyncio
    async def test_calendar_invalid_date_range(self, calendar_engine):
        # End before start should still work (0 entries)
        result = await calendar_engine.generate_calendar(
            start_date="2026-04-30",
            end_date="2026-04-01",
        )
        assert "calendar" in result

    @pytest.mark.asyncio
    async def test_calendar_unknown_industry(self, calendar_engine):
        result = await calendar_engine.generate_calendar(
            industry="underwater_basket_weaving",
            start_date="2026-04-01",
            end_date="2026-04-07",
        )
        assert "calendar" in result

    @pytest.mark.asyncio
    async def test_translate_same_language(self, multilingual_engine):
        result = await multilingual_engine.translate_copy(
            copy_text="Hello world",
            target_language="en",
            source_language="en",
        )
        assert "translated" in result

    @pytest.mark.asyncio
    async def test_batch_translate_empty_list(self, multilingual_engine):
        result = await multilingual_engine.batch_translate(
            copy_text="Hello",
            target_languages=[],
        )
        assert result["languages_count"] == 0

    def test_brand_voice_profile_empty(self):
        profile = BrandVoiceProfile(brand_name="Empty")
        fragment = profile.to_prompt_fragment()
        assert "Empty" in fragment

    def test_calendar_entry_defaults(self):
        entry = CalendarEntry(
            date="2026-01-01",
            day_of_week="Thursday",
            time="10:00",
            channel="blog",
            content_type="article",
            content_category="educational",
            title="Test",
            description="Test desc",
        )
        assert entry.status == "planned"
        assert entry.priority == "medium"
        assert entry.related_event is None
        assert entry.tags == []
