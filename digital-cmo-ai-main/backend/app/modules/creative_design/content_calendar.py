"""
Smart Content Calendar for the Creative & Design Module.

Generates intelligent content calendars that account for:
- Product launch dates and campaign milestones
- Seasonal and holiday events
- Industry-specific events and awareness dates
- Optimal posting times per platform
- Content mix and frequency best practices
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field
from typing import Optional


# ── Optimal Posting Times (UTC) ─────────────────────────────────────────

OPTIMAL_POSTING_TIMES: dict[str, dict] = {
    "linkedin": {
        "best_days": ["Tuesday", "Wednesday", "Thursday"],
        "best_hours": ["08:00", "10:00", "12:00"],
        "worst_days": ["Saturday", "Sunday"],
        "frequency": "3-5 posts per week",
        "notes": "B2B audiences are most active mid-week during business hours.",
    },
    "twitter": {
        "best_days": ["Monday", "Tuesday", "Wednesday", "Thursday"],
        "best_hours": ["09:00", "12:00", "17:00"],
        "worst_days": ["Sunday"],
        "frequency": "1-3 tweets per day",
        "notes": "Engagement peaks during commute times and lunch breaks.",
    },
    "instagram": {
        "best_days": ["Tuesday", "Wednesday", "Friday"],
        "best_hours": ["11:00", "13:00", "19:00"],
        "worst_days": ["Sunday"],
        "frequency": "3-7 posts per week",
        "notes": "Visual content performs best around lunch and evening.",
    },
    "facebook": {
        "best_days": ["Wednesday", "Thursday", "Friday"],
        "best_hours": ["09:00", "13:00", "16:00"],
        "worst_days": ["Saturday"],
        "frequency": "3-5 posts per week",
        "notes": "Afternoon posts tend to get more shares.",
    },
    "email": {
        "best_days": ["Tuesday", "Wednesday", "Thursday"],
        "best_hours": ["06:00", "10:00", "14:00"],
        "worst_days": ["Saturday", "Sunday"],
        "frequency": "1-2 emails per week",
        "notes": "Morning sends have higher open rates for B2B.",
    },
    "blog": {
        "best_days": ["Monday", "Tuesday", "Wednesday"],
        "best_hours": ["09:00", "11:00"],
        "worst_days": ["Saturday", "Sunday"],
        "frequency": "1-4 posts per week",
        "notes": "Publish early in the week for maximum initial traffic.",
    },
    "youtube": {
        "best_days": ["Thursday", "Friday", "Saturday"],
        "best_hours": ["12:00", "15:00", "18:00"],
        "worst_days": ["Monday"],
        "frequency": "1-2 videos per week",
        "notes": "Publish before the weekend for maximum watch time.",
    },
    "sms": {
        "best_days": ["Tuesday", "Wednesday", "Thursday"],
        "best_hours": ["10:00", "12:00", "14:00"],
        "worst_days": ["Sunday"],
        "frequency": "2-4 messages per month",
        "notes": "Avoid early morning and late evening. Respect quiet hours.",
    },
}


# ── Seasonal Events ─────────────────────────────────────────────────────

SEASONAL_EVENTS: list[dict] = [
    {"name": "New Year", "month": 1, "day": 1, "type": "holiday", "prep_days": 14},
    {"name": "Valentine's Day", "month": 2, "day": 14, "type": "holiday", "prep_days": 14},
    {"name": "International Women's Day", "month": 3, "day": 8, "type": "awareness", "prep_days": 7},
    {"name": "Earth Day", "month": 4, "day": 22, "type": "awareness", "prep_days": 7},
    {"name": "Mother's Day (US)", "month": 5, "day": 12, "type": "holiday", "prep_days": 14},
    {"name": "Father's Day (US)", "month": 6, "day": 15, "type": "holiday", "prep_days": 14},
    {"name": "Back to School", "month": 8, "day": 15, "type": "seasonal", "prep_days": 21},
    {"name": "Labor Day (US)", "month": 9, "day": 1, "type": "holiday", "prep_days": 7},
    {"name": "Halloween", "month": 10, "day": 31, "type": "holiday", "prep_days": 21},
    {"name": "Black Friday", "month": 11, "day": 28, "type": "shopping", "prep_days": 30},
    {"name": "Cyber Monday", "month": 11, "day": 30, "type": "shopping", "prep_days": 30},
    {"name": "Christmas", "month": 12, "day": 25, "type": "holiday", "prep_days": 30},
    {"name": "End of Year / New Year's Eve", "month": 12, "day": 31, "type": "holiday", "prep_days": 14},
]

# ── Industry-Specific Events ────────────────────────────────────────────

INDUSTRY_EVENTS: dict[str, list[dict]] = {
    "technology": [
        {"name": "CES", "month": 1, "day": 7, "type": "conference", "prep_days": 14},
        {"name": "MWC (Mobile World Congress)", "month": 2, "day": 24, "type": "conference", "prep_days": 14},
        {"name": "Google I/O", "month": 5, "day": 14, "type": "conference", "prep_days": 7},
        {"name": "WWDC (Apple)", "month": 6, "day": 9, "type": "conference", "prep_days": 7},
        {"name": "AWS re:Invent", "month": 11, "day": 28, "type": "conference", "prep_days": 14},
    ],
    "marketing": [
        {"name": "SXSW", "month": 3, "day": 7, "type": "conference", "prep_days": 14},
        {"name": "Content Marketing World", "month": 9, "day": 21, "type": "conference", "prep_days": 14},
        {"name": "HubSpot INBOUND", "month": 9, "day": 3, "type": "conference", "prep_days": 14},
        {"name": "Advertising Week", "month": 10, "day": 14, "type": "conference", "prep_days": 7},
    ],
    "finance": [
        {"name": "Q1 Earnings Season", "month": 4, "day": 15, "type": "financial", "prep_days": 7},
        {"name": "Q2 Earnings Season", "month": 7, "day": 15, "type": "financial", "prep_days": 7},
        {"name": "Q3 Earnings Season", "month": 10, "day": 15, "type": "financial", "prep_days": 7},
        {"name": "Tax Season Deadline (US)", "month": 4, "day": 15, "type": "deadline", "prep_days": 30},
    ],
    "ecommerce": [
        {"name": "Amazon Prime Day", "month": 7, "day": 12, "type": "shopping", "prep_days": 21},
        {"name": "Singles' Day (11.11)", "month": 11, "day": 11, "type": "shopping", "prep_days": 21},
        {"name": "Small Business Saturday", "month": 11, "day": 29, "type": "shopping", "prep_days": 14},
    ],
    "healthcare": [
        {"name": "World Health Day", "month": 4, "day": 7, "type": "awareness", "prep_days": 7},
        {"name": "Mental Health Awareness Month", "month": 5, "day": 1, "type": "awareness", "prep_days": 14},
        {"name": "Breast Cancer Awareness Month", "month": 10, "day": 1, "type": "awareness", "prep_days": 14},
    ],
}


# ── Content Mix Recommendations ─────────────────────────────────────────

CONTENT_MIX = {
    "educational": {"ratio": 0.40, "description": "How-tos, tips, tutorials, industry insights"},
    "promotional": {"ratio": 0.20, "description": "Product features, offers, launches"},
    "engagement": {"ratio": 0.20, "description": "Polls, questions, user-generated content"},
    "brand_story": {"ratio": 0.10, "description": "Behind-the-scenes, team spotlights, values"},
    "curated": {"ratio": 0.10, "description": "Industry news, partner content, thought leadership"},
}


@dataclass
class CalendarEntry:
    """A single entry in the content calendar."""

    date: str
    day_of_week: str
    time: str
    channel: str
    content_type: str
    content_category: str
    title: str
    description: str
    status: str = "planned"
    priority: str = "medium"
    related_event: Optional[str] = None
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "date": self.date,
            "day_of_week": self.day_of_week,
            "time": self.time,
            "channel": self.channel,
            "content_type": self.content_type,
            "content_category": self.content_category,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "related_event": self.related_event,
            "tags": self.tags,
        }


class ContentCalendarEngine:
    """
    Generates smart, context-aware content calendars.
    """

    def __init__(self, llm_client=None):
        self.llm = llm_client

    async def generate_calendar(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        channels: Optional[list[str]] = None,
        industry: Optional[str] = None,
        product_launches: Optional[list[dict]] = None,
        custom_events: Optional[list[dict]] = None,
        brand_guidelines: str = "",
        timezone_offset: int = 0,
    ) -> dict:
        """
        Generate a comprehensive content calendar.

        Args:
            start_date: Calendar start (YYYY-MM-DD). Defaults to today.
            end_date: Calendar end (YYYY-MM-DD). Defaults to 30 days from start.
            channels: List of channels to plan for.
            industry: Industry vertical for relevant events.
            product_launches: List of dicts with 'name', 'date', 'description'.
            custom_events: Additional events to incorporate.
            brand_guidelines: Brand voice and content guidelines.
            timezone_offset: Hours offset from UTC.

        Returns:
            Dict with calendar entries, events, and metadata.
        """
        now = datetime.now(timezone.utc)
        start = self._parse_date(start_date) if start_date else now
        end = self._parse_date(end_date) if end_date else start + timedelta(days=30)

        channels = channels or ["linkedin", "twitter", "blog", "email"]
        product_launches = product_launches or []
        custom_events = custom_events or []

        # Gather relevant events in the date range
        relevant_events = self._gather_events(start, end, industry, product_launches, custom_events)

        # Generate calendar entries
        entries = self._build_calendar_entries(
            start=start,
            end=end,
            channels=channels,
            events=relevant_events,
            timezone_offset=timezone_offset,
        )

        # Optionally use LLM to enrich content ideas
        if self.llm and entries:
            entries = await self._enrich_with_llm(entries, brand_guidelines)

        return {
            "calendar": [e.to_dict() for e in entries],
            "date_range": {
                "start": start.strftime("%Y-%m-%d"),
                "end": end.strftime("%Y-%m-%d"),
                "total_days": (end - start).days,
            },
            "channels": channels,
            "events_included": [
                {"name": e["name"], "date": e.get("date", ""), "type": e.get("type", "")}
                for e in relevant_events
            ],
            "content_mix": CONTENT_MIX,
            "posting_guidelines": {
                ch: OPTIMAL_POSTING_TIMES.get(ch, {}) for ch in channels
            },
            "total_entries": len(entries),
        }

    def _gather_events(
        self,
        start: datetime,
        end: datetime,
        industry: Optional[str],
        product_launches: list[dict],
        custom_events: list[dict],
    ) -> list[dict]:
        """Collect all relevant events within the date range."""
        events = []
        year = start.year

        # Seasonal events
        for se in SEASONAL_EVENTS:
            try:
                event_date = datetime(year, se["month"], se["day"], tzinfo=timezone.utc)
                if start <= event_date <= end:
                    events.append({**se, "date": event_date.strftime("%Y-%m-%d")})
            except ValueError:
                pass

        # Industry events
        if industry and industry.lower() in INDUSTRY_EVENTS:
            for ie in INDUSTRY_EVENTS[industry.lower()]:
                try:
                    event_date = datetime(year, ie["month"], ie["day"], tzinfo=timezone.utc)
                    if start <= event_date <= end:
                        events.append({**ie, "date": event_date.strftime("%Y-%m-%d")})
                except ValueError:
                    pass

        # Product launches
        for pl in product_launches:
            pl_date = pl.get("date", "")
            if pl_date:
                try:
                    parsed = datetime.strptime(pl_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                    if start <= parsed <= end:
                        events.append({
                            "name": pl.get("name", "Product Launch"),
                            "date": pl_date,
                            "type": "product_launch",
                            "prep_days": pl.get("prep_days", 14),
                            "description": pl.get("description", ""),
                        })
                except ValueError:
                    pass

        # Custom events
        for ce in custom_events:
            ce_date = ce.get("date", "")
            if ce_date:
                events.append({
                    "name": ce.get("name", "Custom Event"),
                    "date": ce_date,
                    "type": ce.get("type", "custom"),
                    "prep_days": ce.get("prep_days", 7),
                })

        return events

    def _build_calendar_entries(
        self,
        start: datetime,
        end: datetime,
        channels: list[str],
        events: list[dict],
        timezone_offset: int = 0,
    ) -> list[CalendarEntry]:
        """Build calendar entries based on channels, events, and best practices."""
        entries: list[CalendarEntry] = []
        current = start
        content_categories = list(CONTENT_MIX.keys())
        cat_index = 0

        while current <= end:
            day_name = current.strftime("%A")

            for channel in channels:
                posting_info = OPTIMAL_POSTING_TIMES.get(channel, {})
                best_days = posting_info.get("best_days", ["Monday", "Wednesday", "Friday"])
                best_hours = posting_info.get("best_hours", ["10:00"])
                worst_days = posting_info.get("worst_days", [])

                # Skip worst days
                if day_name in worst_days:
                    continue

                # Post on best days, or every other day for non-best days
                if day_name in best_days:
                    post_time = best_hours[0] if best_hours else "10:00"
                elif (current - start).days % 3 == 0:
                    post_time = best_hours[-1] if best_hours else "14:00"
                else:
                    continue

                # Adjust for timezone
                hour = int(post_time.split(":")[0]) + timezone_offset
                adjusted_time = f"{hour % 24:02d}:00"

                # Check if this date relates to an event
                related_event = None
                priority = "medium"
                for event in events:
                    event_date_str = event.get("date", "")
                    if event_date_str:
                        try:
                            event_date = datetime.strptime(event_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                            days_until = (event_date - current).days
                            prep_days = event.get("prep_days", 7)
                            if 0 <= days_until <= prep_days:
                                related_event = event["name"]
                                priority = "high" if days_until <= 3 else "medium"
                                break
                        except ValueError:
                            pass

                # Rotate content categories
                category = content_categories[cat_index % len(content_categories)]
                cat_index += 1

                # Determine content type based on channel
                content_type = self._channel_content_type(channel)

                # Build title and description
                if related_event:
                    title = f"{related_event} — {channel.title()} {content_type}"
                    description = f"Content for {related_event} on {channel}."
                else:
                    title = f"{category.replace('_', ' ').title()} — {channel.title()}"
                    description = f"{CONTENT_MIX[category]['description']} for {channel}."

                entries.append(CalendarEntry(
                    date=current.strftime("%Y-%m-%d"),
                    day_of_week=day_name,
                    time=adjusted_time,
                    channel=channel,
                    content_type=content_type,
                    content_category=category,
                    title=title,
                    description=description,
                    status="planned",
                    priority=priority,
                    related_event=related_event,
                    tags=[category, channel],
                ))

            current += timedelta(days=1)

        return entries

    @staticmethod
    def _channel_content_type(channel: str) -> str:
        """Map a channel to its primary content type."""
        mapping = {
            "linkedin": "post",
            "twitter": "tweet",
            "instagram": "post",
            "facebook": "post",
            "email": "newsletter",
            "blog": "article",
            "youtube": "video",
            "sms": "message",
        }
        return mapping.get(channel.lower(), "post")

    async def _enrich_with_llm(
        self, entries: list[CalendarEntry], guidelines: str
    ) -> list[CalendarEntry]:
        """Use the LLM to generate better titles and descriptions for entries."""
        # Batch the first 15 entries for enrichment to avoid excessive API calls
        batch = entries[:15]
        summaries = []
        for e in batch:
            summaries.append(
                f"- {e.date} | {e.channel} | {e.content_category} | Event: {e.related_event or 'none'}"
            )

        prompt = (
            "You are a content strategist. For each calendar entry below, suggest a "
            "specific, creative content title and a one-sentence description.\n\n"
            f"Brand guidelines: {guidelines or 'General professional brand.'}\n\n"
            "Entries:\n" + "\n".join(summaries) + "\n\n"
            "Return a JSON array where each item has 'title' and 'description'. "
            "Output ONLY valid JSON."
        )

        raw = await self._call_llm(prompt)
        try:
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0]
            suggestions = json.loads(cleaned)
            if isinstance(suggestions, list):
                for i, suggestion in enumerate(suggestions):
                    if i < len(entries):
                        entries[i].title = suggestion.get("title", entries[i].title)
                        entries[i].description = suggestion.get("description", entries[i].description)
        except (json.JSONDecodeError, TypeError):
            pass  # Keep original titles

        return entries

    @staticmethod
    def _parse_date(date_str: str) -> datetime:
        """Parse a YYYY-MM-DD string into a timezone-aware datetime."""
        return datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)

    async def _call_llm(self, prompt: str) -> str:
        """Call the LLM."""
        if self.llm:
            try:
                messages = [
                    {"role": "system", "content": "You are a content strategist and calendar planner."},
                    {"role": "user", "content": prompt},
                ]
                return await self.llm.generate(messages)
            except Exception as e:
                return f"[Calendar Error: {str(e)}]"
        return "[]"

    def get_optimal_times(self, channel: str) -> dict:
        """Return optimal posting times for a given channel."""
        return OPTIMAL_POSTING_TIMES.get(channel.lower(), {})

    def get_seasonal_events(self, month: Optional[int] = None) -> list[dict]:
        """Return seasonal events, optionally filtered by month."""
        if month:
            return [e for e in SEASONAL_EVENTS if e["month"] == month]
        return SEASONAL_EVENTS

    def get_industry_events(self, industry: str) -> list[dict]:
        """Return events for a specific industry."""
        return INDUSTRY_EVENTS.get(industry.lower(), [])
