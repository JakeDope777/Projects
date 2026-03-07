'''
Google Analytics Connector

Implements the ConnectorInterface for Google Analytics.
Returns demo data when credentials are not configured.
'''

import logging
import random
from typing import Optional, Any, Dict
from datetime import datetime, timedelta

from .base import ConnectorInterface

logger = logging.getLogger(__name__)


class GoogleAnalyticsConnector(ConnectorInterface):
    """Connector for Google Analytics API."""

    BASE_URL = "https://analyticsdata.googleapis.com/v1beta"

    def __init__(self, property_id: Optional[str] = None, access_token: Optional[str] = None):
        super().__init__(service_name="GoogleAnalytics", rate_limit=50, rate_window=60)
        self.property_id = property_id
        self._access_token = access_token
        if not self.property_id or not self._access_token:
            self._enter_demo_mode("Missing property_id or access_token.")

    async def authenticate(self) -> None:
        """Authenticates with Google Analytics using OAuth2."""
        if self._access_token and self.property_id:
            self._is_authenticated = True
            logger.info("Google Analytics connector authenticated with provided token.")
        else:
            self._enter_demo_mode("Missing property_id or access_token.")

    async def get_data(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Fetch data from a specific API endpoint."""
        if self._demo_mode:
            return self._generate_demo_data(endpoint, params)

        await self._ensure_authenticated()
        headers = {"Authorization": f"Bearer {self._access_token}"}
        url = f"{self.BASE_URL}/{endpoint}"
        return await self._request_with_retry("GET", url, headers=headers, params=params)

    async def post_data(self, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Send data to a specific API endpoint."""
        if self._demo_mode:
            return {"status": "success", "message": "Demo mode, no data posted."}

        await self._ensure_authenticated()
        headers = {"Authorization": f"Bearer {self._access_token}"}
        url = f"{self.BASE_URL}/{endpoint}"
        return await self._request_with_retry("POST", url, headers=headers, json_data=data)

    async def get_website_metrics(
        self,
        start_date: str = "30daysAgo",
        end_date: str = "today",
    ) -> Dict:
        """Retrieves core website metrics for a date range."""
        if self._demo_mode:
            return {
                "demo": True,
                "metrics": {
                    "active_users": random.randint(1000, 10000),
                    "new_users": random.randint(300, 4000),
                    "sessions": random.randint(1500, 15000),
                    "bounce_rate": round(random.uniform(0.2, 0.6), 4),
                },
                "top_pages": [
                    {"path": "/", "views": random.randint(1000, 5000)},
                    {"path": "/pricing", "views": random.randint(500, 2500)},
                    {"path": "/blog/ai-marketing", "views": random.randint(300, 2000)},
                ],
            }

        endpoint = f"properties/{self.property_id}:runReport"
        report_request = {
            "dateRanges": [{"startDate": start_date, "endDate": end_date}],
            "metrics": [
                {"name": "activeUsers"},
                {"name": "newUsers"},
                {"name": "sessions"},
                {"name": "bounceRate"},
                {"name": "averageSessionDuration"},
            ],
        }
        return await self.post_data(endpoint, data={"reportRequests": [report_request]})

    async def get_realtime_data(self) -> Dict:
        """Gets real-time active users."""
        endpoint = f"properties/{self.property_id}:runRealtimeReport"
        report_request = {"metrics": [{"name": "activeUsers"}]}
        return await self.post_data(endpoint, data={"reportRequests": [report_request]})

    async def get_audience_overview(self, start_date: str, end_date: str) -> Dict:
        """Provides an overview of the audience demographics."""
        endpoint = f"properties/{self.property_id}:runReport"
        report_request = {
            "dateRanges": [{"startDate": start_date, "endDate": end_date}],
            "dimensions": [{"name": "country"}, {"name": "userAgeBracket"}],
            "metrics": [{"name": "activeUsers"}],
        }
        return await self.post_data(endpoint, data={"reportRequests": [report_request]})

    async def get_traffic_sources(self, start_date: str, end_date: str) -> Dict:
        """Identifies the top traffic sources."""
        endpoint = f"properties/{self.property_id}:runReport"
        report_request = {
            "dateRanges": [{"startDate": start_date, "endDate": end_date}],
            "dimensions": [{"name": "sessionDefaultChannelGroup"}],
            "metrics": [{"name": "sessions"}],
            "orderBys": [{"metric": {"metricName": "sessions"}, "desc": True}],
            "limit": 5,
        }
        return await self.post_data(endpoint, data={"reportRequests": [report_request]})

    async def get_top_pages(self, start_date: str, end_date: str) -> Dict:
        """Lists the most viewed pages."""
        endpoint = f"properties/{self.property_id}:runReport"
        report_request = {
            "dateRanges": [{"startDate": start_date, "endDate": end_date}],
            "dimensions": [{"name": "pagePath"}],
            "metrics": [{"name": "screenPageViews"}],
            "orderBys": [{"metric": {"metricName": "screenPageViews"}, "desc": True}],
            "limit": 10,
        }
        return await self.post_data(endpoint, data={"reportRequests": [report_request]})

    async def get_conversion_data(self, start_date: str, end_date: str) -> Dict:
        """Retrieves data on goal completions."""
        endpoint = f"properties/{self.property_id}:runReport"
        report_request = {
            "dateRanges": [{"startDate": start_date, "endDate": end_date}],
            "dimensions": [{"name": "eventName"}],
            "metrics": [{"name": "conversions"}],
            "orderBys": [{"metric": {"metricName": "conversions"}, "desc": True}],
        }
        return await self.post_data(endpoint, data={"reportRequests": [report_request]})

    def _generate_demo_data(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Generates realistic mock data for Google Analytics."""
        if "runReport" in endpoint:
            return {
                "kind": "analyticsData#runReport",
                "rowCount": random.randint(50, 200),
                "rows": [
                    {
                        "dimensionValues": [{"value": f"demo_{i}"} for i in range(random.randint(1, 3))],
                        "metricValues": [{"value": str(random.randint(100, 10000))} for _ in range(random.randint(1, 5))]
                    } for _ in range(10)
                ],
            }
        if "runRealtimeReport" in endpoint:
            return {
                "kind": "analyticsData#runRealtimeReport",
                "rowCount": 1,
                "rows": [{"metricValues": [{"value": str(random.randint(5, 50))}]}],
            }
        return {}
