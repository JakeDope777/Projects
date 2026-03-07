"""
Data Sources Package

Provides unified access to external data sources for business analysis:
- NewsAPI: Industry news and current events
- Google Trends (pytrends): Search interest and trending topics
- Wikipedia API: Background information and industry context
- Web Scraper: General-purpose web data extraction
"""

from .news_api import NewsAPIClient
from .google_trends import GoogleTrendsClient
from .wikipedia_api import WikipediaClient
from .web_scraper import WebScraper

__all__ = [
    "NewsAPIClient",
    "GoogleTrendsClient",
    "WikipediaClient",
    "WebScraper",
]
