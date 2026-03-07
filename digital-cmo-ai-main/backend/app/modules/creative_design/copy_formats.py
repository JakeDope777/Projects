"""
Copy Format Definitions for the Creative & Design Module.

Each format describes a specific marketing content type with its own
structural template, length constraints, and platform-specific guidance.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class CopyFormat:
    """Specification for a single copy format."""

    name: str
    display_name: str
    description: str
    prompt_template: str
    default_length: int  # approximate word count
    min_length: int
    max_length: int
    platform: Optional[str] = None
    structural_hints: list[str] = field(default_factory=list)

    def build_prompt(self, brief: str, tone_fragment: str, guidelines: str,
                     language: str = "English", extra_context: str = "") -> str:
        """Render the full LLM prompt for this format."""
        return self.prompt_template.format(
            brief=brief,
            tone_fragment=tone_fragment,
            guidelines=guidelines,
            language=language,
            extra_context=extra_context,
            default_length=self.default_length,
            structural_hints="\n".join(f"- {h}" for h in self.structural_hints),
        )


# ── Format Definitions ──────────────────────────────────────────────────

BLOG_POST = CopyFormat(
    name="blog_post",
    display_name="Blog Post",
    description="Long-form blog article with SEO-friendly structure.",
    default_length=800,
    min_length=300,
    max_length=3000,
    structural_hints=[
        "Include a compelling headline",
        "Use H2/H3 sub-headings for scannability",
        "Open with a hook that addresses the reader's pain point",
        "Include a clear call-to-action at the end",
        "Optimise for SEO with natural keyword placement",
    ],
    prompt_template=(
        "Write a blog post based on the following brief.\n\n"
        "Brief: {brief}\n"
        "{tone_fragment}\n"
        "Target length: ~{default_length} words\n"
        "Language: {language}\n"
        "Brand guidelines: {guidelines}\n"
        "{extra_context}\n\n"
        "Structural requirements:\n{structural_hints}\n\n"
        "Produce the full blog post in Markdown format."
    ),
)

SOCIAL_CAPTION = CopyFormat(
    name="social_caption",
    display_name="Social Media Caption",
    description="Short-form caption for Instagram, Facebook, or general social media.",
    default_length=50,
    min_length=10,
    max_length=200,
    platform="social",
    structural_hints=[
        "Keep it concise and scroll-stopping",
        "Include a hook in the first line",
        "End with a call-to-action or question",
        "Suggest 3-5 relevant hashtags",
    ],
    prompt_template=(
        "Write a social media caption.\n\n"
        "Brief: {brief}\n"
        "{tone_fragment}\n"
        "Target length: ~{default_length} words\n"
        "Language: {language}\n"
        "Brand guidelines: {guidelines}\n"
        "{extra_context}\n\n"
        "Requirements:\n{structural_hints}"
    ),
)

EMAIL_SUBJECT = CopyFormat(
    name="email_subject",
    display_name="Email Subject Line",
    description="High-open-rate email subject lines.",
    default_length=10,
    min_length=3,
    max_length=20,
    platform="email",
    structural_hints=[
        "Generate 5 subject line options",
        "Keep each under 60 characters",
        "Use power words that drive opens",
        "Include at least one personalisation token option (e.g. {first_name})",
        "Avoid spam trigger words",
    ],
    prompt_template=(
        "Generate email subject lines.\n\n"
        "Brief: {brief}\n"
        "{tone_fragment}\n"
        "Language: {language}\n"
        "Brand guidelines: {guidelines}\n"
        "{extra_context}\n\n"
        "Requirements:\n{structural_hints}"
    ),
)

AD_HEADLINE = CopyFormat(
    name="ad_headline",
    display_name="Ad Headline",
    description="Punchy headlines for paid advertising (Google Ads, Meta Ads, etc.).",
    default_length=15,
    min_length=5,
    max_length=30,
    platform="advertising",
    structural_hints=[
        "Generate 5 headline options",
        "Keep each under 30 characters for Google Ads compatibility",
        "Include a value proposition or benefit",
        "Use action verbs",
        "At least one option should include a number or statistic",
    ],
    prompt_template=(
        "Generate ad headlines.\n\n"
        "Brief: {brief}\n"
        "{tone_fragment}\n"
        "Language: {language}\n"
        "Brand guidelines: {guidelines}\n"
        "{extra_context}\n\n"
        "Requirements:\n{structural_hints}"
    ),
)

PRODUCT_DESCRIPTION = CopyFormat(
    name="product_description",
    display_name="Product Description",
    description="Compelling product descriptions for e-commerce or landing pages.",
    default_length=150,
    min_length=50,
    max_length=500,
    structural_hints=[
        "Lead with the primary benefit",
        "Include key features as bullet points",
        "Address the target customer's pain point",
        "End with a persuasive call-to-action",
        "Use sensory and emotional language",
    ],
    prompt_template=(
        "Write a product description.\n\n"
        "Brief: {brief}\n"
        "{tone_fragment}\n"
        "Target length: ~{default_length} words\n"
        "Language: {language}\n"
        "Brand guidelines: {guidelines}\n"
        "{extra_context}\n\n"
        "Requirements:\n{structural_hints}"
    ),
)

LINKEDIN_POST = CopyFormat(
    name="linkedin_post",
    display_name="LinkedIn Post",
    description="Professional LinkedIn post optimised for engagement.",
    default_length=150,
    min_length=50,
    max_length=500,
    platform="linkedin",
    structural_hints=[
        "Open with a bold statement or surprising insight (the hook)",
        "Use short paragraphs (1-2 sentences each) for mobile readability",
        "Include a personal anecdote or data point",
        "End with a question or call-to-action to drive comments",
        "Suggest 3-5 relevant hashtags",
        "Use line breaks generously for readability",
    ],
    prompt_template=(
        "Write a LinkedIn post.\n\n"
        "Brief: {brief}\n"
        "{tone_fragment}\n"
        "Target length: ~{default_length} words\n"
        "Language: {language}\n"
        "Brand guidelines: {guidelines}\n"
        "{extra_context}\n\n"
        "Requirements:\n{structural_hints}"
    ),
)

TWITTER_THREAD = CopyFormat(
    name="twitter_thread",
    display_name="Twitter/X Thread",
    description="Multi-tweet thread for Twitter/X with engagement hooks.",
    default_length=200,
    min_length=100,
    max_length=500,
    platform="twitter",
    structural_hints=[
        "Write 5-10 tweets, each under 280 characters",
        "Number each tweet (1/, 2/, etc.)",
        "First tweet must be a compelling hook that makes people want to read on",
        "Last tweet should include a call-to-action (follow, retweet, reply)",
        "Include a 'save this thread' prompt",
        "Use simple, direct language",
    ],
    prompt_template=(
        "Write a Twitter/X thread.\n\n"
        "Brief: {brief}\n"
        "{tone_fragment}\n"
        "Language: {language}\n"
        "Brand guidelines: {guidelines}\n"
        "{extra_context}\n\n"
        "Requirements:\n{structural_hints}"
    ),
)

YOUTUBE_SCRIPT = CopyFormat(
    name="youtube_script",
    display_name="YouTube Video Script",
    description="Structured video script with hooks, segments, and CTAs.",
    default_length=600,
    min_length=200,
    max_length=2000,
    platform="youtube",
    structural_hints=[
        "Start with a 15-second hook that previews the value",
        "Include an intro segment with channel branding",
        "Break content into clearly labelled segments/chapters",
        "Add B-roll / visual suggestions in [brackets]",
        "Include a mid-roll CTA (subscribe, like)",
        "End with a summary and end-screen CTA",
        "Write in spoken-word style (contractions, natural pacing)",
    ],
    prompt_template=(
        "Write a YouTube video script.\n\n"
        "Brief: {brief}\n"
        "{tone_fragment}\n"
        "Target length: ~{default_length} words\n"
        "Language: {language}\n"
        "Brand guidelines: {guidelines}\n"
        "{extra_context}\n\n"
        "Requirements:\n{structural_hints}"
    ),
)

PRESS_RELEASE = CopyFormat(
    name="press_release",
    display_name="Press Release",
    description="Formal press release following AP style conventions.",
    default_length=500,
    min_length=300,
    max_length=1000,
    structural_hints=[
        "Include a dateline (city, date)",
        "Write a strong headline and optional sub-headline",
        "Lead paragraph must answer Who, What, When, Where, Why",
        "Include a quote from a company spokesperson",
        "Add a boilerplate 'About [Company]' section at the end",
        "Follow inverted pyramid structure",
        "End with media contact information placeholder",
    ],
    prompt_template=(
        "Write a press release.\n\n"
        "Brief: {brief}\n"
        "{tone_fragment}\n"
        "Target length: ~{default_length} words\n"
        "Language: {language}\n"
        "Brand guidelines: {guidelines}\n"
        "{extra_context}\n\n"
        "Requirements:\n{structural_hints}"
    ),
)

LANDING_PAGE = CopyFormat(
    name="landing_page",
    display_name="Landing Page Copy",
    description="Conversion-focused landing page copy with sections.",
    default_length=400,
    min_length=200,
    max_length=1500,
    platform="web",
    structural_hints=[
        "Write a hero section with headline, sub-headline, and CTA button text",
        "Include a 'Problem' section that resonates with the target audience",
        "Include a 'Solution' section highlighting key benefits (3-4 bullet points)",
        "Add a social proof section (testimonial placeholders)",
        "Include a features section with brief descriptions",
        "Write a final CTA section with urgency",
        "Label each section clearly for the developer",
    ],
    prompt_template=(
        "Write landing page copy.\n\n"
        "Brief: {brief}\n"
        "{tone_fragment}\n"
        "Target length: ~{default_length} words\n"
        "Language: {language}\n"
        "Brand guidelines: {guidelines}\n"
        "{extra_context}\n\n"
        "Requirements:\n{structural_hints}"
    ),
)

SMS_CAMPAIGN = CopyFormat(
    name="sms_campaign",
    display_name="SMS Campaign",
    description="Short, high-impact SMS marketing messages.",
    default_length=25,
    min_length=10,
    max_length=50,
    platform="sms",
    structural_hints=[
        "Generate 3-5 SMS variants",
        "Keep each message under 160 characters",
        "Include a clear CTA with a link placeholder",
        "Use urgency or exclusivity where appropriate",
        "Include opt-out language: 'Reply STOP to unsubscribe'",
        "Comply with TCPA and GDPR guidelines",
    ],
    prompt_template=(
        "Write SMS campaign messages.\n\n"
        "Brief: {brief}\n"
        "{tone_fragment}\n"
        "Language: {language}\n"
        "Brand guidelines: {guidelines}\n"
        "{extra_context}\n\n"
        "Requirements:\n{structural_hints}"
    ),
)

# ── Registry ────────────────────────────────────────────────────────────

FORMAT_REGISTRY: dict[str, CopyFormat] = {
    "blog_post": BLOG_POST,
    "social_caption": SOCIAL_CAPTION,
    "email_subject": EMAIL_SUBJECT,
    "ad_headline": AD_HEADLINE,
    "product_description": PRODUCT_DESCRIPTION,
    "linkedin_post": LINKEDIN_POST,
    "twitter_thread": TWITTER_THREAD,
    "youtube_script": YOUTUBE_SCRIPT,
    "press_release": PRESS_RELEASE,
    "landing_page": LANDING_PAGE,
    "sms_campaign": SMS_CAMPAIGN,
}


def get_format(name: str) -> CopyFormat:
    """Return a copy format by name, falling back to *blog_post*."""
    return FORMAT_REGISTRY.get(name.lower(), BLOG_POST)


def list_formats() -> list[str]:
    """Return all available format names."""
    return list(FORMAT_REGISTRY.keys())
