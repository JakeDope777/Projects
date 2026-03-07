"""
Google Trends Client

Wraps the pytrends library to provide async-friendly access to
Google Trends data for search interest analysis, related queries,
regional interest, and trending topics.
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=3)


class GoogleTrendsClient:
    """
    Async wrapper around pytrends for Google Trends data.

    All heavy I/O is delegated to a thread pool so the event loop
    remains responsive.
    """

    def __init__(self, hl: str = "en-US", tz: int = 360, timeout: tuple = (10, 25)):
        self.hl = hl
        self.tz = tz
        self.timeout = timeout
        self._pytrends = None

    def _get_pytrends(self):
        """Lazy-initialise the pytrends TrendReq object."""
        if self._pytrends is None:
            try:
                from pytrends.request import TrendReq
                self._pytrends = TrendReq(
                    hl=self.hl, tz=self.tz, timeout=self.timeout
                )
            except ImportError:
                logger.error(
                    "pytrends is not installed. "
                    "Install with: pip install pytrends"
                )
                raise
        return self._pytrends

    async def get_interest_over_time(
        self,
        keywords: list[str],
        timeframe: str = "today 12-m",
        geo: str = "",
    ) -> dict:
        """
        Retrieve search interest over time for up to 5 keywords.

        Args:
            keywords: List of search terms (max 5).
            timeframe: Timeframe string (e.g. 'today 12-m', 'today 3-m').
            geo: Geographic region code (e.g. 'US', 'GB', '').

        Returns:
            Dict with 'data' (list of date/value rows), 'keywords',
            'timeframe', and 'generated_at'.
        """
        keywords = keywords[:5]
        loop = asyncio.get_event_loop()

        def _fetch():
            pt = self._get_pytrends()
            pt.build_payload(keywords, timeframe=timeframe, geo=geo)
            df = pt.interest_over_time()
            return df

        try:
            df = await loop.run_in_executor(_executor, _fetch)
            if df is None or df.empty:
                return self._empty_result(keywords, timeframe)

            if "isPartial" in df.columns:
                df = df.drop(columns=["isPartial"])

            records = []
            for date_idx, row in df.iterrows():
                record = {"date": date_idx.strftime("%Y-%m-%d")}
                for kw in keywords:
                    if kw in row:
                        record[kw] = int(row[kw])
                records.append(record)

            return {
                "data": records,
                "keywords": keywords,
                "timeframe": timeframe,
                "geo": geo,
                "generated_at": datetime.utcnow().isoformat(),
            }

        except Exception as exc:
            logger.error("Google Trends interest_over_time failed: %s", exc)
            return self._empty_result(keywords, timeframe)

    async def get_related_queries(
        self,
        keyword: str,
        timeframe: str = "today 12-m",
        geo: str = "",
    ) -> dict:
        """
        Retrieve related queries (top and rising) for a keyword.

        Returns:
            Dict with 'top' and 'rising' lists of query dicts.
        """
        loop = asyncio.get_event_loop()

        def _fetch():
            pt = self._get_pytrends()
            pt.build_payload([keyword], timeframe=timeframe, geo=geo)
            return pt.related_queries()

        try:
            result = await loop.run_in_executor(_executor, _fetch)
            if not result or keyword not in result:
                return {"top": [], "rising": [], "keyword": keyword}

            kw_data = result[keyword]
            top_df = kw_data.get("top")
            rising_df = kw_data.get("rising")

            top = top_df.to_dict("records") if top_df is not None and not top_df.empty else []
            rising = rising_df.to_dict("records") if rising_df is not None and not rising_df.empty else []

            return {
                "top": top[:20],
                "rising": rising[:20],
                "keyword": keyword,
                "timeframe": timeframe,
                "generated_at": datetime.utcnow().isoformat(),
            }

        except Exception as exc:
            logger.error("Google Trends related_queries failed: %s", exc)
            return {"top": [], "rising": [], "keyword": keyword}

    async def get_related_topics(
        self,
        keyword: str,
        timeframe: str = "today 12-m",
        geo: str = "",
    ) -> dict:
        """
        Retrieve related topics (top and rising) for a keyword.

        Returns:
            Dict with 'top' and 'rising' lists of topic dicts.
        """
        loop = asyncio.get_event_loop()

        def _fetch():
            pt = self._get_pytrends()
            pt.build_payload([keyword], timeframe=timeframe, geo=geo)
            return pt.related_topics()

        try:
            result = await loop.run_in_executor(_executor, _fetch)
            if not result or keyword not in result:
                return {"top": [], "rising": [], "keyword": keyword}

            kw_data = result[keyword]
            top_df = kw_data.get("top")
            rising_df = kw_data.get("rising")

            top = top_df.to_dict("records") if top_df is not None and not top_df.empty else []
            rising = rising_df.to_dict("records") if rising_df is not None and not rising_df.empty else []

            return {
                "top": top[:20],
                "rising": rising[:20],
                "keyword": keyword,
                "timeframe": timeframe,
                "generated_at": datetime.utcnow().isoformat(),
            }

        except Exception as exc:
            logger.error("Google Trends related_topics failed: %s", exc)
            return {"top": [], "rising": [], "keyword": keyword}

    async def get_interest_by_region(
        self,
        keywords: list[str],
        timeframe: str = "today 12-m",
        resolution: str = "COUNTRY",
    ) -> dict:
        """
        Retrieve search interest broken down by geographic region.

        Args:
            keywords: Search terms (max 5).
            timeframe: Timeframe string.
            resolution: One of 'COUNTRY', 'REGION', 'CITY', 'DMA'.

        Returns:
            Dict with 'data' (list of region/value rows) and metadata.
        """
        keywords = keywords[:5]
        loop = asyncio.get_event_loop()

        def _fetch():
            pt = self._get_pytrends()
            pt.build_payload(keywords, timeframe=timeframe)
            return pt.interest_by_region(resolution=resolution)

        try:
            df = await loop.run_in_executor(_executor, _fetch)
            if df is None or df.empty:
                return {"data": [], "keywords": keywords}

            df = df[(df > 0).any(axis=1)]
            df = df.sort_values(by=keywords[0], ascending=False).head(30)

            records = []
            for region, row in df.iterrows():
                record = {"region": region}
                for kw in keywords:
                    if kw in row:
                        record[kw] = int(row[kw])
                records.append(record)

            return {
                "data": records,
                "keywords": keywords,
                "resolution": resolution,
                "generated_at": datetime.utcnow().isoformat(),
            }

        except Exception as exc:
            logger.error("Google Trends interest_by_region failed: %s", exc)
            return {"data": [], "keywords": keywords}

    async def get_trending_searches(self, country: str = "united_states") -> list[str]:
        """
        Retrieve today's trending searches for a country.

        Returns:
            List of trending search strings.
        """
        loop = asyncio.get_event_loop()

        def _fetch():
            pt = self._get_pytrends()
            df = pt.trending_searches(pn=country)
            return df[0].tolist() if not df.empty else []

        try:
            return await loop.run_in_executor(_executor, _fetch)
        except Exception as exc:
            logger.error("Google Trends trending_searches failed: %s", exc)
            return []

    @staticmethod
    def _empty_result(keywords: list[str], timeframe: str) -> dict:
        return {
            "data": [],
            "keywords": keywords,
            "timeframe": timeframe,
            "generated_at": datetime.utcnow().isoformat(),
        }
