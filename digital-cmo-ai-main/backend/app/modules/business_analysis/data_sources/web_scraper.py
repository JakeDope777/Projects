"""
Web Scraper

General-purpose async web scraper for extracting structured data
from web pages. Used for competitor research, market data collection,
and content analysis.
"""

import asyncio
import logging
import re
from typing import Optional
from urllib.parse import urljoin, urlparse

import httpx

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


class WebScraper:
    """
    Async web scraper for extracting page content, metadata,
    and structured data from websites.
    """

    def __init__(
        self,
        timeout: float = 15.0,
        max_retries: int = 2,
        headers: Optional[dict] = None,
    ):
        self.timeout = timeout
        self.max_retries = max_retries
        self.headers = headers or DEFAULT_HEADERS

    async def fetch_page(self, url: str) -> dict:
        """
        Fetch a web page and extract its content.

        Args:
            url: The URL to fetch.

        Returns:
            Dict with 'url', 'status_code', 'title', 'meta_description',
            'text_content', 'headings', 'links', and 'raw_html'.
        """
        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(
                    timeout=self.timeout,
                    follow_redirects=True,
                    headers=self.headers,
                ) as client:
                    response = await client.get(url)
                    response.raise_for_status()

                return self._parse_html(url, response.text, response.status_code)

            except httpx.HTTPStatusError as exc:
                logger.warning(
                    "HTTP %s for %s (attempt %d)",
                    exc.response.status_code, url, attempt + 1,
                )
                if attempt == self.max_retries:
                    return self._error_result(url, str(exc))
            except Exception as exc:
                logger.warning(
                    "Fetch failed for %s (attempt %d): %s",
                    url, attempt + 1, exc,
                )
                if attempt == self.max_retries:
                    return self._error_result(url, str(exc))
                await asyncio.sleep(1)

        return self._error_result(url, "Max retries exceeded")

    async def fetch_multiple(self, urls: list[str], concurrency: int = 5) -> list[dict]:
        """
        Fetch multiple pages concurrently.

        Args:
            urls: List of URLs to fetch.
            concurrency: Maximum number of concurrent requests.

        Returns:
            List of page result dicts.
        """
        semaphore = asyncio.Semaphore(concurrency)

        async def _bounded_fetch(u: str) -> dict:
            async with semaphore:
                return await self.fetch_page(u)

        tasks = [_bounded_fetch(u) for u in urls]
        return await asyncio.gather(*tasks)

    async def extract_company_data(self, url: str) -> dict:
        """
        Extract company-relevant data from a website.

        Attempts to identify company name, description, social links,
        contact information, and key page content.

        Args:
            url: Company website URL.

        Returns:
            Dict with extracted company data.
        """
        page = await self.fetch_page(url)
        if page.get("error"):
            return {"url": url, "error": page["error"]}

        domain = urlparse(url).netloc

        social_links = {}
        for link in page.get("links", []):
            href = link.get("href", "")
            if "linkedin.com" in href:
                social_links["linkedin"] = href
            elif "twitter.com" in href or "x.com" in href:
                social_links["twitter"] = href
            elif "facebook.com" in href:
                social_links["facebook"] = href
            elif "instagram.com" in href:
                social_links["instagram"] = href
            elif "youtube.com" in href:
                social_links["youtube"] = href
            elif "github.com" in href:
                social_links["github"] = href

        emails = self._extract_emails(page.get("text_content", ""))
        phones = self._extract_phones(page.get("text_content", ""))

        return {
            "url": url,
            "domain": domain,
            "title": page.get("title", ""),
            "meta_description": page.get("meta_description", ""),
            "headings": page.get("headings", []),
            "social_links": social_links,
            "emails": emails[:5],
            "phones": phones[:5],
            "text_preview": (page.get("text_content", ""))[:1000],
        }

    async def search_and_scrape(
        self,
        query: str,
        search_engine_url: str = "https://html.duckduckgo.com/html/",
        max_results: int = 5,
    ) -> list[dict]:
        """
        Search using DuckDuckGo HTML and scrape top results.

        Args:
            query: Search query.
            search_engine_url: Search engine URL.
            max_results: Number of results to scrape.

        Returns:
            List of scraped page dicts.
        """
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                headers=self.headers,
            ) as client:
                response = await client.post(
                    search_engine_url,
                    data={"q": query},
                )
                response.raise_for_status()

            urls = self._extract_search_urls(response.text, max_results)
            if not urls:
                return []

            return await self.fetch_multiple(urls)

        except Exception as exc:
            logger.error("Search and scrape failed for '%s': %s", query, exc)
            return []

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _parse_html(self, url: str, html: str, status_code: int) -> dict:
        """Parse HTML content and extract structured data."""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
        except ImportError:
            return {
                "url": url,
                "status_code": status_code,
                "title": self._regex_extract_title(html),
                "meta_description": "",
                "text_content": self._strip_tags(html)[:5000],
                "headings": [],
                "links": [],
            }

        title = soup.title.string.strip() if soup.title and soup.title.string else ""

        meta_desc = ""
        meta_tag = soup.find("meta", attrs={"name": "description"})
        if meta_tag:
            meta_desc = meta_tag.get("content", "")

        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        text_content = soup.get_text(separator=" ", strip=True)
        text_content = re.sub(r"\s+", " ", text_content)[:5000]

        headings = []
        for level in range(1, 4):
            for h in soup.find_all(f"h{level}"):
                text = h.get_text(strip=True)
                if text:
                    headings.append({"level": level, "text": text})

        links = []
        for a in soup.find_all("a", href=True)[:50]:
            href = a["href"]
            if href.startswith(("http://", "https://")):
                links.append({
                    "href": href,
                    "text": a.get_text(strip=True)[:100],
                })
            elif href.startswith("/"):
                links.append({
                    "href": urljoin(url, href),
                    "text": a.get_text(strip=True)[:100],
                })

        return {
            "url": url,
            "status_code": status_code,
            "title": title,
            "meta_description": meta_desc,
            "text_content": text_content,
            "headings": headings,
            "links": links,
        }

    @staticmethod
    def _extract_search_urls(html: str, max_results: int) -> list[str]:
        """Extract result URLs from DuckDuckGo HTML search results."""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            urls = []
            for a in soup.select("a.result__a"):
                href = a.get("href", "")
                if href.startswith(("http://", "https://")):
                    urls.append(href)
                if len(urls) >= max_results:
                    break
            return urls
        except ImportError:
            pattern = r'class="result__a"[^>]*href="(https?://[^"]+)"'
            matches = re.findall(pattern, html)
            return matches[:max_results]

    @staticmethod
    def _extract_emails(text: str) -> list[str]:
        """Extract email addresses from text."""
        pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        return list(set(re.findall(pattern, text)))

    @staticmethod
    def _extract_phones(text: str) -> list[str]:
        """Extract phone numbers from text."""
        pattern = r"[\+]?[(]?[0-9]{1,4}[)]?[-\s\./0-9]{7,15}"
        matches = re.findall(pattern, text)
        return [m.strip() for m in set(matches) if len(m.strip()) >= 10]

    @staticmethod
    def _regex_extract_title(html: str) -> str:
        """Fallback title extraction using regex."""
        match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
        return match.group(1).strip() if match else ""

    @staticmethod
    def _strip_tags(html: str) -> str:
        """Remove HTML tags using regex."""
        return re.sub(r"<[^>]+>", " ", html)

    @staticmethod
    def _error_result(url: str, error: str) -> dict:
        return {
            "url": url,
            "status_code": 0,
            "title": "",
            "meta_description": "",
            "text_content": "",
            "headings": [],
            "links": [],
            "error": error,
        }
