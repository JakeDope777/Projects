"""
Creative & Design API endpoints — Expanded Edition.

POST /creative/generate          - Generate marketing copy (11 formats, 6 tones, 5 languages)
POST /creative/image             - Generate visual assets / image prompts
POST /creative/ab-test           - Generate and score A/B test variants
POST /creative/schedule          - Create content schedule (legacy)
POST /creative/calendar          - Generate smart content calendar
POST /creative/brand-voice/learn - Learn brand voice from samples
POST /creative/brand-voice/check - Check copy against brand voice
POST /creative/translate         - Translate and adapt copy
POST /creative/translate/batch   - Batch translate into multiple languages
GET  /creative/capabilities      - List available tones, formats, and languages
"""

from fastapi import APIRouter, Depends

from ..db.schemas import (
    CopyGenerationRequest,
    ImageGenerationRequest,
    ABTestRequest,
    ContentScheduleRequest,
    ContentCalendarRequest,
    BrandVoiceLearnRequest,
    BrandVoiceCheckRequest,
    TranslationRequest,
    BatchTranslationRequest,
    CreativeResponse,
    ABTestResponse,
    ContentCalendarResponse,
    BrandVoiceResponse,
    TranslationResponse,
    CapabilitiesResponse,
)
from ..modules.creative_design import CreativeDesignModule

router = APIRouter(prefix="/creative", tags=["Creative & Design"])

_module = CreativeDesignModule()


def get_module() -> CreativeDesignModule:
    return _module


# ── Copy Generation ─────────────────────────────────────────────────────

@router.post("/generate", response_model=CreativeResponse)
async def generate_copy(
    request: CopyGenerationRequest,
    module: CreativeDesignModule = Depends(get_module),
):
    """Generate marketing copy in any supported format, tone, and language."""
    result = await module.generate_copy(
        brief=request.brief,
        tone=request.tone,
        copy_format=request.copy_format,
        length=request.length,
        language=request.language,
        brand_name=request.brand_name,
        context=request.context,
    )
    return CreativeResponse(
        content=result.get("content"),
        alternatives=result.get("alternatives"),
        metadata=result.get("metadata"),
    )


# ── Image Generation ────────────────────────────────────────────────────

@router.post("/image", response_model=CreativeResponse)
async def generate_image(
    request: ImageGenerationRequest,
    module: CreativeDesignModule = Depends(get_module),
):
    """Generate a visual asset or detailed image prompt."""
    result = await module.generate_image(
        description=request.description,
        style=request.style,
        brand_name=request.brand_name,
        context=request.context,
    )
    return CreativeResponse(
        content=result.get("content"),
        image_url=result.get("image_url"),
    )


# ── A/B Testing ─────────────────────────────────────────────────────────

@router.post("/ab-test", response_model=ABTestResponse)
async def suggest_ab_tests(
    request: ABTestRequest,
    module: CreativeDesignModule = Depends(get_module),
):
    """Generate 3-5 A/B test variants with predicted performance scores."""
    result = await module.suggest_ab_tests(
        base_copy=request.base_copy,
        num_variants=request.num_variants,
        brand_name=request.brand_name,
        context=request.context,
    )
    return ABTestResponse(
        base_copy=result.get("base_copy", request.base_copy),
        num_variants=result.get("num_variants", 0),
        variants=result.get("variants"),
        recommended_variant=result.get("recommended_variant"),
        scoring_dimensions=result.get("scoring_dimensions"),
        summary=result.get("summary"),
    )


# ── Content Schedule (Legacy) ───────────────────────────────────────────

@router.post("/schedule", response_model=CreativeResponse)
async def create_content_schedule(
    request: ContentScheduleRequest,
    module: CreativeDesignModule = Depends(get_module),
):
    """Generate a content schedule (legacy endpoint)."""
    result = await module.create_content_schedule(
        events=request.events,
        context=request.context,
    )
    return CreativeResponse(schedule=result.get("schedule"))


# ── Smart Content Calendar ──────────────────────────────────────────────

@router.post("/calendar", response_model=ContentCalendarResponse)
async def create_content_calendar(
    request: ContentCalendarRequest,
    module: CreativeDesignModule = Depends(get_module),
):
    """Generate a smart content calendar with events, optimal times, and content mix."""
    result = await module.create_content_calendar(
        start_date=request.start_date,
        end_date=request.end_date,
        channels=request.channels,
        industry=request.industry,
        product_launches=request.product_launches,
        custom_events=request.custom_events,
        brand_name=request.brand_name,
        context=request.context,
    )
    return ContentCalendarResponse(
        calendar=result.get("calendar"),
        date_range=result.get("date_range"),
        channels=result.get("channels"),
        events_included=result.get("events_included"),
        content_mix=result.get("content_mix"),
        posting_guidelines=result.get("posting_guidelines"),
        total_entries=result.get("total_entries", 0),
    )


# ── Brand Voice ─────────────────────────────────────────────────────────

@router.post("/brand-voice/learn", response_model=BrandVoiceResponse)
async def learn_brand_voice(
    request: BrandVoiceLearnRequest,
    module: CreativeDesignModule = Depends(get_module),
):
    """Analyse writing samples to build a brand voice profile."""
    result = await module.learn_brand_voice(
        brand_name=request.brand_name,
        samples=request.samples,
    )
    return BrandVoiceResponse(
        profile=result.get("profile"),
        prompt_fragment=result.get("prompt_fragment"),
        message=result.get("message"),
    )


@router.post("/brand-voice/check", response_model=BrandVoiceResponse)
async def check_brand_consistency(
    request: BrandVoiceCheckRequest,
    module: CreativeDesignModule = Depends(get_module),
):
    """Check if copy is consistent with a brand voice profile."""
    result = await module.check_brand_consistency(
        brand_name=request.brand_name,
        copy_text=request.copy_text,
    )
    return BrandVoiceResponse(
        scores=result.get("scores"),
        suggestions=result.get("suggestions"),
        revised_copy=result.get("revised_copy"),
        message=result.get("error"),
    )


# ── Translation ─────────────────────────────────────────────────────────

@router.post("/translate", response_model=TranslationResponse)
async def translate_copy(
    request: TranslationRequest,
    module: CreativeDesignModule = Depends(get_module),
):
    """Translate and culturally adapt marketing copy."""
    result = await module.translate_copy(
        copy_text=request.copy_text,
        target_language=request.target_language,
        source_language=request.source_language,
        formality=request.formality,
    )
    return TranslationResponse(
        original=result.get("original"),
        translated=result.get("translated"),
        source_language=result.get("source_language"),
        target_language=result.get("target_language"),
        formality=result.get("formality"),
    )


@router.post("/translate/batch", response_model=TranslationResponse)
async def batch_translate(
    request: BatchTranslationRequest,
    module: CreativeDesignModule = Depends(get_module),
):
    """Translate copy into multiple languages at once."""
    result = await module.batch_translate(
        copy_text=request.copy_text,
        target_languages=request.target_languages,
        source_language=request.source_language,
    )
    return TranslationResponse(
        original=result.get("original"),
        source_language=result.get("source_language"),
        translations=result.get("translations"),
        languages_count=result.get("languages_count", 0),
    )


# ── Capabilities ────────────────────────────────────────────────────────

@router.get("/capabilities", response_model=CapabilitiesResponse)
async def get_capabilities(
    module: CreativeDesignModule = Depends(get_module),
):
    """List all available tones, formats, languages, and brand profiles."""
    return CapabilitiesResponse(
        tones=module.get_available_tones(),
        formats=module.get_available_formats(),
        languages=module.get_available_languages(),
        brand_profiles=module.get_brand_profiles(),
    )
