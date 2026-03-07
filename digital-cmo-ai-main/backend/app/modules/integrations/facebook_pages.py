'''
Facebook Pages Connector

Implements the ConnectorInterface for Facebook Pages.
Returns demo data when credentials are not configured.
'''

import logging
import random
from typing import Optional, Any, Dict
from datetime import datetime, timedelta

from .base import ConnectorInterface, ConnectorError

logger = logging.getLogger(__name__)


class FacebookPagesConnector(ConnectorInterface):
    """Connector for Facebook Pages API."""

    BASE_URL = "https://graph.facebook.com/v19.0"

    def __init__(self, page_id: Optional[str] = None, page_access_token: Optional[str] = None):
        super().__init__(service_name="FacebookPages", rate_limit=60)
        self.page_id = page_id
        self.page_access_token = page_access_token

    async def authenticate(self) -> None:
        """Validate credentials and enter demo mode if not provided."""
        if not self.page_id or not self.page_access_token:
            self._enter_demo_mode("Missing Page ID or Page Access Token")
            return

        try:
            # Test authentication by fetching basic page info
            await self.get_data(f"/{self.page_id}", {"fields": "id,name"})
            self._is_authenticated = True
            logger.info("Facebook Pages authentication successful.")
        except ConnectorError as e:
            self._is_authenticated = False
            logger.error(f"Facebook Pages authentication failed: {e}")
            raise

    async def get_data(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Fetch data from a specific API endpoint."""
        if self._demo_mode:
            return self._generate_demo_data("GET", endpoint, params)

        await self._ensure_authenticated()
        url = f"{self.BASE_URL}{endpoint}"
        headers = {"Authorization": f"Bearer {self.page_access_token}"}
        return await self._request_with_retry("GET", url, headers=headers, params=params)

    async def post_data(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send data to a specific API endpoint."""
        if self._demo_mode:
            return self._generate_demo_data("POST", endpoint, data)

        await self._ensure_authenticated()
        url = f"{self.BASE_URL}{endpoint}"
        headers = {"Authorization": f"Bearer {self.page_access_token}"}
        return await self._request_with_retry("POST", url, headers=headers, json_data=data)

    async def create_page_post(self, message: str) -> Dict[str, Any]:
        """Creates a new post on the Facebook Page."""
        return await self.post_data(f"/{self.page_id}/feed", data={"message": message})

    async def get_page_insights(self, metrics: list[str], since: datetime, until: datetime) -> Dict[str, Any]:
        """Retrieves insights for the Facebook Page."""
        params = {
            "metric": ",".join(metrics),
            "period": "day",
            "since": int(since.timestamp()),
            "until": int(until.timestamp()),
        }
        return await self.get_data(f"/{self.page_id}/insights", params)

    async def get_page_posts(self, limit: int = 10) -> Dict[str, Any]:
        """Retrieves the most recent posts from the Facebook Page."""
        return await self.get_data(f"/{self.page_id}/posts", {"limit": limit})

    async def schedule_post(self, message: str, scheduled_time: datetime) -> Dict[str, Any]:
        """Schedules a post to be published at a future time."""
        params = {
            "message": message,
            "published": "false",
            "scheduled_publish_time": int(scheduled_time.timestamp()),
        }
        return await self.post_data(f"/{self.page_id}/feed", data=params)

    async def get_post_engagement(self, post_id: str) -> Dict[str, Any]:
        """Retrieves engagement metrics for a specific post."""
        params = {"fields": "likes.summary(true),comments.summary(true),shares"}
        return await self.get_data(f"/{post_id}", params)

    async def get_page_fans(self) -> Dict[str, Any]:
        """Retrieves the total number of fans (likes) for the page."""
        return await self.get_data(f"/{self.page_id}", {"fields": "fan_count"})

    def _generate_demo_data(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generates realistic mock data for demo mode."""
        if method == "POST":
            if "feed" in endpoint:
                return {"id": f"{self.page_id or '12345'}_{random.randint(100000, 999999)}"}
            return {"success": True}

        if "insights" in endpoint:
            return {
                "data": [
                    {
                        "name": "page_impressions",
                        "period": "day",
                        "values": [
                            {"value": random.randint(1000, 5000), "end_time": (datetime.now() - timedelta(days=1)).isoformat()},
                            {"value": random.randint(1000, 5000), "end_time": datetime.now().isoformat()},
                        ],
                    }
                ]
            }
        if "posts" in endpoint or "feed" in endpoint:
            return {
                "data": [
                    {
                        "id": f"{self.page_id or '12345'}_{random.randint(100000, 999999)}",
                        "message": "This is a demo post from Manus AI!",
                        "created_time": datetime.now().isoformat(),
                    }
                    for _ in range(data.get("limit", 10) if data else 10)
                ]
            }
        if "fan_count" in endpoint:
            return {"fan_count": random.randint(5000, 100000), "id": self.page_id or '12345'}

        if "likes" in endpoint:
             return {
                "likes": {"data": [], "summary": {"total_count": random.randint(10, 500)}},
                "comments": {"data": [], "summary": {"total_count": random.randint(5, 100)}},
                "shares": {"count": random.randint(1, 50)},
                "id": f"{self.page_id or '12345'}_{random.randint(100000, 999999)}",
            }

        return {}
