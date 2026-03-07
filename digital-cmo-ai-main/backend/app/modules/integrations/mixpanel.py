'''
Mixpanel Connector

Implements the ConnectorInterface for Mixpanel.
Returns demo data when credentials are not configured.
'''

import base64
import logging
import random
from typing import Optional, Any, Dict
from datetime import datetime, timedelta

from .base import ConnectorInterface

logger = logging.getLogger(__name__)


class MixpanelConnector(ConnectorInterface):
    """Connector for Mixpanel API."""

    BASE_URL = "https://mixpanel.com/api/2.0"

    def __init__(self, api_secret: Optional[str] = None, project_id: Optional[str] = None):
        super().__init__(service_name="Mixpanel", rate_limit=60)
        self.api_secret = api_secret
        self.project_id = project_id
        self.headers = {}

    async def authenticate(self) -> None:
        """Authenticate with Mixpanel using API secret."""
        if self.api_secret:
            try:
                encoded_secret = base64.b64encode(f"{self.api_secret}:".encode("utf-8")).decode("utf-8")
                self.headers = {
                    "Authorization": f"Basic {encoded_secret}",
                    "Content-Type": "application/json",
                }
                # Test authentication by making a simple request
                await self.get_events(limit=1)
                self._is_authenticated = True
                logger.info("Mixpanel authentication successful.")
            except Exception as e:
                logger.error(f"Mixpanel authentication failed: {e}")
                self._enter_demo_mode("Authentication failed")
        else:
            self._enter_demo_mode()

    async def get_data(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """Fetch data from a specific API endpoint."""
        if self._demo_mode:
            return self._generate_demo_data(endpoint, params)

        await self._ensure_authenticated()
        url = f"{self.BASE_URL}{endpoint}"
        return await self._request_with_retry("GET", url, headers=self.headers, params=params)

    async def post_data(self, endpoint: str, data: Optional[dict] = None) -> dict:
        """Send data to a specific API endpoint."""
        if self._demo_mode:
            return self._generate_demo_data(endpoint, data)

        await self._ensure_authenticated()
        url = f"{self.BASE_URL}{endpoint}"
        return await self._request_with_retry("POST", url, headers=self.headers, json_data=data)

    async def get_events(self, limit: int = 100) -> Dict[str, Any]:
        """Get a list of recent events."""
        return await self.get_data("/events", params={"limit": limit})

    async def get_funnel_data(self, funnel_id: int, from_date: str, to_date: str) -> Dict[str, Any]:
        """Get data for a specific funnel."""
        params = {
            "funnel_id": funnel_id,
            "from_date": from_date,
            "to_date": to_date,
        }
        return await self.get_data("/funnels", params=params)

    async def get_retention_data(self, from_date: str, to_date: str) -> Dict[str, Any]:
        """Get retention data."""
        params = {
            "from_date": from_date,
            "to_date": to_date,
        }
        return await self.get_data("/retention", params=params)

    async def track_event(self, event_name: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Track a single event."""
        event_data = {
            "event": event_name,
            "properties": {
                "token": self.project_id,  # Assuming project_id is the token
                "distinct_id": properties.get("distinct_id", "default_user"),
                **properties,
            },
        }
        # Mixpanel's track endpoint is different
        track_url = "https://api.mixpanel.com/track"
        if self._demo_mode:
            return self._generate_demo_data("/track", event_data)

        await self._ensure_authenticated()
        return await self._request_with_retry("POST", track_url, headers=self.headers, json_data=[event_data])

    async def get_user_profiles(self, limit: int = 100) -> Dict[str, Any]:
        """Get user profiles."""
        return await self.get_data("/engage", params={"limit": limit})

    async def get_segmentation_data(self, event: str, from_date: str, to_date: str) -> Dict[str, Any]:
        """Get segmentation data for an event."""
        params = {
            "event": event,
            "from_date": from_date,
            "to_date": to_date,
        }
        return await self.get_data("/segmentation", params=params)

    def _generate_demo_data(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """Generate realistic mock data for demo mode."""
        today = datetime.utcnow().date()
        if endpoint == "/events":
            return {
                "events": [
                    {
                        "event": random.choice(["Signed Up", "Purchased", "Viewed Page"]),
                        "properties": {
                            "time": (today - timedelta(days=random.randint(0, 30))).isoformat(),
                            "distinct_id": f"user_{random.randint(1, 1000)}",
                            "page": f"/page/{random.randint(1, 10)}",
                        },
                    }
                    for _ in range(params.get("limit", 10))
                ]
            }
        if endpoint == "/funnels":
            return {
                "funnel_id": params.get("funnel_id", 1),
                "steps": [
                    {"event": "Signed Up", "count": random.randint(500, 1000)},
                    {"event": "Activated", "count": random.randint(300, 500)},
                    {"event": "Purchased", "count": random.randint(100, 300)},
                ],
            }
        if endpoint == "/retention":
            return {
                "retention": {
                    "2023-01-01": [100, 50, 30, 20],
                    "2023-01-02": [120, 60, 40, 25],
                }
            }
        if endpoint == "/track":
            return {"status": 1, "error": None}
        if endpoint == "/engage":
            return {
                "results": [
                    {
                        "$distinct_id": f"user_{random.randint(1, 1000)}",
                        "$properties": {
                            "$email": f"user{random.randint(1, 1000)}@example.com",
                            "$created": (today - timedelta(days=random.randint(0, 90))).isoformat(),
                        },
                    }
                    for _ in range(params.get("limit", 10))
                ]
            }
        if endpoint == "/segmentation":
            return {
                "data": {
                    "series": ["2023-01-01", "2023-01-02"],
                    "values": {
                        "Segment1": [random.randint(100, 200), random.randint(150, 250)],
                        "Segment2": [random.randint(50, 100), random.randint(75, 125)],
                    },
                }
            }
        return {}
