"""
NewsAPI Client

Fetches industry news, headlines, and articles from the NewsAPI service.
Provides structured news data for market research and trend monitoring.
Supports filtering by topic, date range, language, and source.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

DEFAULT_PAGE_SIZE = 10
NEWSAPI_BASE_URL = "https://newsapi.org/v2"


class NewsAPIClient:
    """
    Async client for the NewsAPI service.

    Provides methods to search for news articles, fetch top headlines,
    and extract structured data for business analysis.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self._base_url = NEWSAPI_BASE_URL

    @property
    def is_configured(self) -> bool:
        """Check whether an API key has been provided."""
        return bool(self.api_key)

    async def search_news(
        self,
        query: str,
        days_back: int = 30,
        language: str = "en",
        sort_by: str = "relevancy",
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> list[dict]:
        """
        Search for news articles matching a query.

        Args:
            query: Search keywords or phrase.
            days_back: How many days back to search (max 30 for free tier).
            language: ISO 639-1 language code.
            sort_by: One of 'relevancy', 'popularity', 'publishedAt'.
            page_size: Number of results to return (max 100).

        Returns:
            List of article dicts with title, description, url, source,
            published_at, and content fields.
        """
        if not self.is_configured:
            logger.warning("NewsAPI key not configured; returning empty results.")
            return []

        from_date = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%d")

        params = {
            "q": query,
            "from": from_date,
            "language": language,
            "sortBy": sort_by,
            "pageSize": min(page_size, 100),
            "apiKey": self.api_key,
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(f"{self._base_url}/everything", params=params)
                response.raise_for_status()
                data = response.json()

            articles = data.get("articles", [])
            return [self._normalize_article(a) for a in articles]

        except httpx.HTTPStatusError as exc:
            logger.error("NewsAPI HTTP error %s: %s", exc.response.status_code, exc.response.text)
            return []
        except Exception as exc:
            logger.error("NewsAPI request failed: %s", exc)
            return []

    async def get_top_headlines(
        self,
        category: Optional[str] = None,
        country: str = "us",
        query: Optional[str] = None,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> list[dict]:
        """
        Fetch top headlines, optionally filtered by category.

        Args:
            category: One of business, entertainment, general, health,
                      science, sports, technology.
            country: ISO 3166-1 alpha-2 country code.
            query: Optional keyword filter.
            page_size: Number of results.

        Returns:
            List of normalised article dicts.
        """
        if not self.is_configured:
            logger.warning("NewsAPI key not configured; returning empty results.")
            return []

        params: dict = {
            "country": country,
            "pageSize": min(page_size, 100),
            "apiKey": self.api_key,
        }
        if category:
            params["category"] = category
        if query:
            params["q"] = query

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(f"{self._base_url}/top-headlines", params=params)
                response.raise_for_status()
                data = response.json()

            articles = data.get("articles", [])
            return [self._normalize_article(a) for a in articles]

        except Exception as exc:
            logger.error("NewsAPI headlines request failed: %s", exc)
            return []

    async def search_industry_news(
        self,
        industry: str,
        additional_keywords: Optional[list[str]] = None,
        days_back: int = 14,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> dict:
        """
        Convenience method: search for industry-specific news and return
        structured results with metadata.

        Args:
            industry: Industry name (e.g. 'fintech', 'healthcare').
            additional_keywords: Extra terms to include in the search.
            days_back: Look-back window in days.
            page_size: Number of articles.

        Returns:
            Dict with 'articles', 'query_used', 'total_results', and
            'date_range' keys.
        """
        keywords = [industry]
        if additional_keywords:
            keywords.extend(additional_keywords)
        query = " OR ".join(keywords)

        articles = await self.search_news(
            query=query,
            days_back=days_back,
            page_size=page_size,
        )

        from_date = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        to_date = datetime.utcnow().strftime("%Y-%m-%d")

        return {
            "articles": articles,
            "query_used": query,
            "total_results": len(articles),
            "date_range": {"from": from_date, "to": to_date},
            "industry": industry,
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_article(raw: dict) -> dict:
        """Convert a raw NewsAPI article to a consistent internal format."""
        source = raw.get("source", {})
        return {
            "title": raw.get("title", ""),
            "description": raw.get("description", ""),
            "url": raw.get("url", ""),
            "source_name": source.get("name", "Unknown"),
            "source_id": source.get("id"),
            "author": raw.get("author"),
            "published_at": raw.get("publishedAt", ""),
            "content_snippet": (raw.get("content") or "")[:500],
            "image_url": raw.get("urlToImage"),
        }
