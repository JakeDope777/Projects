"""
Wikipedia API Client

Provides async access to the Wikipedia REST API for retrieving
background information, company summaries, industry overviews,
and structured data for business analysis context.
"""

import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

WIKIPEDIA_API_URL = "https://en.wikipedia.org/api/rest_v1"
WIKIPEDIA_ACTION_API_URL = "https://en.wikipedia.org/w/api.php"


class WikipediaClient:
    """
    Async client for the Wikipedia REST and Action APIs.

    Provides methods to search for articles, retrieve summaries,
    and extract structured content for business analysis.
    """

    def __init__(self, language: str = "en"):
        self.language = language
        self._rest_url = f"https://{language}.wikipedia.org/api/rest_v1"
        self._action_url = f"https://{language}.wikipedia.org/w/api.php"

    async def get_summary(self, title: str) -> dict:
        """
        Retrieve a summary of a Wikipedia article.

        Args:
            title: Article title (e.g. 'Artificial_intelligence').

        Returns:
            Dict with 'title', 'extract', 'description', 'url',
            'thumbnail', and 'content_urls'.
        """
        url = f"{self._rest_url}/page/summary/{title}"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    url,
                    headers={"User-Agent": "DigitalCMO-AI/1.0"},
                )
                response.raise_for_status()
                data = response.json()

            return {
                "title": data.get("title", ""),
                "extract": data.get("extract", ""),
                "description": data.get("description", ""),
                "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
                "thumbnail": data.get("thumbnail", {}).get("source"),
                "page_id": data.get("pageid"),
                "last_modified": data.get("timestamp"),
            }

        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                logger.info("Wikipedia article not found: %s", title)
                return {"title": title, "extract": "", "error": "not_found"}
            logger.error("Wikipedia HTTP error: %s", exc)
            return {"title": title, "extract": "", "error": str(exc)}
        except Exception as exc:
            logger.error("Wikipedia summary request failed: %s", exc)
            return {"title": title, "extract": "", "error": str(exc)}

    async def search(
        self,
        query: str,
        limit: int = 5,
    ) -> list[dict]:
        """
        Search Wikipedia for articles matching a query.

        Args:
            query: Search query string.
            limit: Maximum number of results.

        Returns:
            List of dicts with 'title', 'snippet', and 'page_id'.
        """
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": limit,
            "format": "json",
            "utf8": 1,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    self._action_url,
                    params=params,
                    headers={"User-Agent": "DigitalCMO-AI/1.0"},
                )
                response.raise_for_status()
                data = response.json()

            results = data.get("query", {}).get("search", [])
            return [
                {
                    "title": r.get("title", ""),
                    "snippet": self._strip_html(r.get("snippet", "")),
                    "page_id": r.get("pageid"),
                    "word_count": r.get("wordcount", 0),
                }
                for r in results
            ]

        except Exception as exc:
            logger.error("Wikipedia search failed: %s", exc)
            return []

    async def get_article_sections(self, title: str) -> list[dict]:
        """
        Retrieve the section structure of a Wikipedia article.

        Returns:
            List of dicts with 'title', 'level', and 'index'.
        """
        params = {
            "action": "parse",
            "page": title,
            "prop": "sections",
            "format": "json",
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    self._action_url,
                    params=params,
                    headers={"User-Agent": "DigitalCMO-AI/1.0"},
                )
                response.raise_for_status()
                data = response.json()

            sections = data.get("parse", {}).get("sections", [])
            return [
                {
                    "title": s.get("line", ""),
                    "level": int(s.get("level", 0)),
                    "index": s.get("index", ""),
                }
                for s in sections
            ]

        except Exception as exc:
            logger.error("Wikipedia sections request failed: %s", exc)
            return []

    async def get_company_info(self, company_name: str) -> dict:
        """
        Convenience method to gather company information from Wikipedia.

        Searches for the company, retrieves the best-matching summary,
        and returns structured data.

        Args:
            company_name: Name of the company.

        Returns:
            Dict with company summary, description, and source URL.
        """
        search_results = await self.search(f"{company_name} company", limit=3)

        if not search_results:
            return {
                "company": company_name,
                "found": False,
                "summary": "",
                "source": "",
            }

        best_match = search_results[0]
        summary = await self.get_summary(best_match["title"])

        return {
            "company": company_name,
            "found": True,
            "wikipedia_title": summary.get("title", ""),
            "summary": summary.get("extract", ""),
            "description": summary.get("description", ""),
            "source": summary.get("url", ""),
            "thumbnail": summary.get("thumbnail"),
        }

    async def get_industry_overview(self, industry: str) -> dict:
        """
        Retrieve an overview of an industry from Wikipedia.

        Args:
            industry: Industry name (e.g. 'fintech', 'e-commerce').

        Returns:
            Dict with industry summary, related articles, and sections.
        """
        search_results = await self.search(f"{industry} industry", limit=5)

        if not search_results:
            return {
                "industry": industry,
                "found": False,
                "summary": "",
                "related_articles": [],
            }

        primary = search_results[0]
        summary = await self.get_summary(primary["title"])
        sections = await self.get_article_sections(primary["title"])

        related = [
            {"title": r["title"], "snippet": r["snippet"]}
            for r in search_results[1:]
        ]

        return {
            "industry": industry,
            "found": True,
            "wikipedia_title": summary.get("title", ""),
            "summary": summary.get("extract", ""),
            "description": summary.get("description", ""),
            "source": summary.get("url", ""),
            "sections": sections,
            "related_articles": related,
        }

    @staticmethod
    def _strip_html(text: str) -> str:
        """Remove HTML tags from a string."""
        import re
        return re.sub(r"<[^>]+>", "", text)
