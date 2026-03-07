"""
Tests for Business Analysis Data Sources

Covers NewsAPI client, Google Trends client, Wikipedia client,
and Web Scraper with mocked external API calls.
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch

from app.modules.business_analysis.data_sources.news_api import NewsAPIClient
from app.modules.business_analysis.data_sources.wikipedia_api import WikipediaClient
from app.modules.business_analysis.data_sources.web_scraper import WebScraper
from app.modules.business_analysis.data_sources.google_trends import GoogleTrendsClient


# =========================================================================
# NewsAPI Client Tests
# =========================================================================

class TestNewsAPIClient:
    """Tests for the NewsAPIClient."""

    def test_init_without_key(self):
        client = NewsAPIClient()
        assert client.api_key is None
        assert client.is_configured is False

    def test_init_with_key(self):
        client = NewsAPIClient(api_key="test-key-123")
        assert client.api_key == "test-key-123"
        assert client.is_configured is True

    @pytest.mark.asyncio
    async def test_search_news_no_api_key(self):
        client = NewsAPIClient()
        result = await client.search_news("test query")
        assert result == []

    @pytest.mark.asyncio
    async def test_get_top_headlines_no_api_key(self):
        client = NewsAPIClient()
        result = await client.get_top_headlines()
        assert result == []

    @pytest.mark.asyncio
    async def test_search_industry_news_no_api_key(self):
        client = NewsAPIClient()
        result = await client.search_industry_news("fintech")
        assert result["articles"] == []
        assert result["industry"] == "fintech"
        assert "query_used" in result
        assert "date_range" in result

    @pytest.mark.asyncio
    async def test_search_news_with_mock(self):
        client = NewsAPIClient(api_key="test-key")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "ok",
            "totalResults": 2,
            "articles": [
                {
                    "source": {"id": "test", "name": "Test Source"},
                    "author": "Test Author",
                    "title": "Test Article Title",
                    "description": "Test description",
                    "url": "https://example.com/article",
                    "urlToImage": "https://example.com/image.jpg",
                    "publishedAt": "2025-01-01T00:00:00Z",
                    "content": "Test content here",
                },
                {
                    "source": {"id": None, "name": "Another Source"},
                    "author": None,
                    "title": "Second Article",
                    "description": None,
                    "url": "https://example.com/article2",
                    "urlToImage": None,
                    "publishedAt": "2025-01-02T00:00:00Z",
                    "content": None,
                },
            ],
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = AsyncMock()
            mock_client_instance.get.return_value = mock_response
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_client_instance

            result = await client.search_news("test", days_back=7, page_size=5)

        assert len(result) == 2
        assert result[0]["title"] == "Test Article Title"
        assert result[0]["source_name"] == "Test Source"
        assert result[0]["url"] == "https://example.com/article"
        assert result[1]["author"] is None
        assert result[1]["content_snippet"] == ""

    def test_normalize_article(self):
        raw = {
            "source": {"id": "bbc", "name": "BBC News"},
            "author": "John Doe",
            "title": "Breaking News",
            "description": "Something happened",
            "url": "https://bbc.com/news/1",
            "urlToImage": "https://bbc.com/img.jpg",
            "publishedAt": "2025-03-01T12:00:00Z",
            "content": "Full article content here" * 50,
        }
        result = NewsAPIClient._normalize_article(raw)
        assert result["title"] == "Breaking News"
        assert result["source_name"] == "BBC News"
        assert result["source_id"] == "bbc"
        assert len(result["content_snippet"]) <= 500

    @pytest.mark.asyncio
    async def test_search_industry_news_structure(self):
        client = NewsAPIClient(api_key="test-key")

        with patch.object(client, "search_news", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = [
                {"title": "Fintech News 1", "url": "https://example.com/1"},
            ]

            result = await client.search_industry_news(
                "fintech",
                additional_keywords=["payments", "banking"],
                days_back=7,
            )

        assert result["industry"] == "fintech"
        assert result["total_results"] == 1
        assert "date_range" in result
        assert result["date_range"]["from"] is not None
        assert result["date_range"]["to"] is not None


# =========================================================================
# Wikipedia Client Tests
# =========================================================================

class TestWikipediaClient:
    """Tests for the WikipediaClient."""

    def test_init_default(self):
        client = WikipediaClient()
        assert client.language == "en"

    def test_init_custom_language(self):
        client = WikipediaClient(language="de")
        assert client.language == "de"
        assert "de.wikipedia.org" in client._rest_url

    @pytest.mark.asyncio
    async def test_get_summary_with_mock(self):
        client = WikipediaClient()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "title": "Artificial intelligence",
            "extract": "AI is the simulation of human intelligence.",
            "description": "Branch of computer science",
            "content_urls": {
                "desktop": {"page": "https://en.wikipedia.org/wiki/AI"}
            },
            "thumbnail": {"source": "https://upload.wikimedia.org/thumb.jpg"},
            "pageid": 12345,
            "timestamp": "2025-01-01T00:00:00Z",
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = AsyncMock()
            mock_client_instance.get.return_value = mock_response
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_client_instance

            result = await client.get_summary("Artificial_intelligence")

        assert result["title"] == "Artificial intelligence"
        assert "AI" in result["extract"]
        assert result["page_id"] == 12345

    @pytest.mark.asyncio
    async def test_search_with_mock(self):
        client = WikipediaClient()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "query": {
                "search": [
                    {
                        "title": "Machine learning",
                        "snippet": "<span>Machine</span> learning is...",
                        "pageid": 111,
                        "wordcount": 5000,
                    },
                    {
                        "title": "Deep learning",
                        "snippet": "<span>Deep</span> learning is...",
                        "pageid": 222,
                        "wordcount": 3000,
                    },
                ]
            }
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = AsyncMock()
            mock_client_instance.get.return_value = mock_response
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_client_instance

            result = await client.search("machine learning", limit=5)

        assert len(result) == 2
        assert result[0]["title"] == "Machine learning"
        assert "<span>" not in result[0]["snippet"]  # HTML stripped
        assert result[0]["page_id"] == 111

    @pytest.mark.asyncio
    async def test_get_company_info_not_found(self):
        client = WikipediaClient()

        with patch.object(client, "search", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = []
            result = await client.get_company_info("NonexistentCompany123")

        assert result["found"] is False
        assert result["company"] == "NonexistentCompany123"

    @pytest.mark.asyncio
    async def test_get_industry_overview(self):
        client = WikipediaClient()

        with patch.object(client, "search", new_callable=AsyncMock) as mock_search, \
             patch.object(client, "get_summary", new_callable=AsyncMock) as mock_summary, \
             patch.object(client, "get_article_sections", new_callable=AsyncMock) as mock_sections:

            mock_search.return_value = [
                {"title": "Fintech", "snippet": "Financial technology", "page_id": 1},
                {"title": "Digital banking", "snippet": "Online banking", "page_id": 2},
            ]
            mock_summary.return_value = {
                "title": "Fintech",
                "extract": "Financial technology overview",
                "description": "Industry",
                "url": "https://en.wikipedia.org/wiki/Fintech",
            }
            mock_sections.return_value = [
                {"title": "History", "level": 2, "index": "1"},
            ]

            result = await client.get_industry_overview("fintech")

        assert result["found"] is True
        assert result["industry"] == "fintech"
        assert len(result["related_articles"]) == 1

    def test_strip_html(self):
        assert WikipediaClient._strip_html("<b>bold</b> text") == "bold text"
        assert WikipediaClient._strip_html("no tags") == "no tags"
        assert WikipediaClient._strip_html("<span class='x'>hi</span>") == "hi"


# =========================================================================
# Web Scraper Tests
# =========================================================================

class TestWebScraper:
    """Tests for the WebScraper."""

    def test_init_defaults(self):
        scraper = WebScraper()
        assert scraper.timeout == 15.0
        assert scraper.max_retries == 2

    def test_init_custom(self):
        scraper = WebScraper(timeout=30.0, max_retries=5)
        assert scraper.timeout == 30.0
        assert scraper.max_retries == 5

    @pytest.mark.asyncio
    async def test_fetch_page_with_mock(self):
        scraper = WebScraper()
        mock_html = """
        <html>
        <head><title>Test Page</title>
        <meta name="description" content="A test page">
        </head>
        <body>
        <h1>Main Heading</h1>
        <h2>Sub Heading</h2>
        <p>Some paragraph text here.</p>
        <a href="https://example.com/link1">Link 1</a>
        <a href="/relative">Relative Link</a>
        </body>
        </html>
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = mock_html
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = AsyncMock()
            mock_client_instance.get.return_value = mock_response
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_client_instance

            result = await scraper.fetch_page("https://example.com")

        assert result["title"] == "Test Page"
        assert result["meta_description"] == "A test page"
        assert result["status_code"] == 200
        assert any(h["text"] == "Main Heading" for h in result["headings"])
        assert any(h["text"] == "Sub Heading" for h in result["headings"])

    @pytest.mark.asyncio
    async def test_fetch_page_error(self):
        scraper = WebScraper(max_retries=0)

        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = AsyncMock()
            mock_client_instance.get.side_effect = Exception("Connection failed")
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_client_instance

            result = await scraper.fetch_page("https://example.com")

        assert result.get("error") is not None
        assert result["status_code"] == 0

    def test_extract_emails(self):
        text = "Contact us at info@example.com or support@test.org for help."
        emails = WebScraper._extract_emails(text)
        assert "info@example.com" in emails
        assert "support@test.org" in emails

    def test_extract_phones(self):
        text = "Call us at +1-555-123-4567 or (800) 555-0199"
        phones = WebScraper._extract_phones(text)
        assert len(phones) >= 1

    def test_error_result(self):
        result = WebScraper._error_result("https://example.com", "timeout")
        assert result["url"] == "https://example.com"
        assert result["error"] == "timeout"
        assert result["status_code"] == 0

    @pytest.mark.asyncio
    async def test_extract_company_data_with_mock(self):
        scraper = WebScraper()

        mock_page = {
            "url": "https://company.com",
            "status_code": 200,
            "title": "Company Inc",
            "meta_description": "We build great software",
            "text_content": "Contact: hello@company.com Phone: +1-555-000-1234",
            "headings": [{"level": 1, "text": "Company Inc"}],
            "links": [
                {"href": "https://linkedin.com/company/test", "text": "LinkedIn"},
                {"href": "https://twitter.com/company", "text": "Twitter"},
                {"href": "https://github.com/company", "text": "GitHub"},
            ],
        }

        with patch.object(scraper, "fetch_page", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_page
            result = await scraper.extract_company_data("https://company.com")

        assert result["domain"] == "company.com"
        assert result["title"] == "Company Inc"
        assert "linkedin" in result["social_links"]
        assert "twitter" in result["social_links"]
        assert "github" in result["social_links"]
        assert "hello@company.com" in result["emails"]


# =========================================================================
# Google Trends Client Tests
# =========================================================================

class TestGoogleTrendsClient:
    """Tests for the GoogleTrendsClient."""

    def test_init_defaults(self):
        client = GoogleTrendsClient()
        assert client.hl == "en-US"
        assert client.tz == 360

    def test_init_custom(self):
        client = GoogleTrendsClient(hl="de", tz=120)
        assert client.hl == "de"
        assert client.tz == 120

    def test_empty_result(self):
        result = GoogleTrendsClient._empty_result(["test"], "today 12-m")
        assert result["data"] == []
        assert result["keywords"] == ["test"]
        assert result["timeframe"] == "today 12-m"
        assert "generated_at" in result

    @pytest.mark.asyncio
    async def test_get_interest_over_time_error_handling(self):
        client = GoogleTrendsClient()

        with patch.object(client, "_get_pytrends") as mock_pt:
            mock_pt.side_effect = ImportError("pytrends not installed")
            result = await client.get_interest_over_time(["test"])

        assert result["data"] == []
        assert result["keywords"] == ["test"]

    @pytest.mark.asyncio
    async def test_get_trending_searches_error(self):
        client = GoogleTrendsClient()

        with patch.object(client, "_get_pytrends") as mock_pt:
            mock_pt.side_effect = Exception("API error")
            result = await client.get_trending_searches()

        assert result == []

    @pytest.mark.asyncio
    async def test_keywords_limited_to_five(self):
        client = GoogleTrendsClient()
        keywords = ["a", "b", "c", "d", "e", "f", "g"]

        with patch.object(client, "_get_pytrends") as mock_pt:
            mock_pt.side_effect = Exception("Expected")
            result = await client.get_interest_over_time(keywords)

        # Should have been truncated to 5
        assert len(result["keywords"]) == 5
