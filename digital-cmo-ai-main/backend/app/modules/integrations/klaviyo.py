'''
Klaviyo Connector

Implements the ConnectorInterface for Klaviyo.
Returns demo data when credentials are not configured.
'''

import logging
import random
from typing import Optional, Any
from datetime import datetime, timedelta

from .base import ConnectorInterface, ConnectorError

logger = logging.getLogger(__name__)

class KlaviyoConnector(ConnectorInterface):
    """Connector for Klaviyo API."""

    BASE_URL = "https://a.klaviyo.com/api"

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(service_name="Klaviyo", api_key=api_key, rate_limit=75)
        if not api_key:
            self._enter_demo_mode()

    async def authenticate(self) -> None:
        """Authenticate with the Klaviyo API using an API key."""
        if self._demo_mode:
            self._is_authenticated = False
            return

        if not self.api_key:
            raise ConnectorError("Klaviyo", 401, "API key is missing.", "AUTH_ERROR")

        # Test authentication by making a simple request
        try:
            await self.get_lists()
            self._is_authenticated = True
            logger.info("Klaviyo authentication successful.")
        except ConnectorError as e:
            self._is_authenticated = False
            logger.error(f"Klaviyo authentication failed: {e}")
            raise

    async def get_data(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """Fetch data from a specific API endpoint."""
        if self._demo_mode:
            return self._generate_demo_data(endpoint, params)

        headers = {"Authorization": f"Klaviyo-API-Key {self.api_key}", "revision": "2023-07-15"}
        url = f"{self.BASE_URL}/{endpoint}"
        return await self._request_with_retry("GET", url, headers=headers, params=params)

    async def post_data(self, endpoint: str, data: Optional[dict] = None) -> dict:
        """Send data to a specific API endpoint."""
        if self._demo_mode:
            return {"status": "success", "message": "Demo mode: campaign created successfully."}

        headers = {"Authorization": f"Klaviyo-API-Key {self.api_key}", "revision": "2023-07-15"}
        url = f"{self.BASE_URL}/{endpoint}"
        return await self._request_with_retry("POST", url, headers=headers, json_data=data)

    async def get_profiles(self) -> dict:
        """Get all profiles."""
        return await self.get_data("profiles")

    async def get_lists(self) -> dict:
        """Get all lists."""
        return await self.get_data("lists")

    async def get_campaigns(self) -> dict:
        """Get all campaigns."""
        return await self.get_data("campaigns")

    async def create_campaign(self, campaign_data: dict) -> dict:
        """Create a new campaign."""
        return await self.post_data("campaigns", data=campaign_data)

    async def get_flows(self) -> dict:
        """Get all flows."""
        return await self.get_data("flows")

    async def get_metrics(self) -> dict:
        """Get all metrics."""
        return await self.get_data("metrics")

    def _generate_demo_data(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """Generate realistic mock data for demo mode."""
        if endpoint == "profiles":
            return {
                "data": [
                    {
                        "type": "profile",
                        "id": f"01H{random.randint(1000, 9999)}",
                        "attributes": {
                            "email": f"user{i}@example.com",
                            "first_name": random.choice(["John", "Jane", "Peter", "Mary"]),
                            "last_name": random.choice(["Doe", "Smith", "Jones", "Williams"]),
                        },
                    }
                    for i in range(10)
                ]
            }
        if endpoint == "lists":
            return {
                "data": [
                    {
                        "type": "list",
                        "id": f"LIST{random.randint(100, 999)}",
                        "attributes": {"name": f"Test List {i}"},
                    }
                    for i in range(3)
                ]
            }
        if endpoint == "campaigns":
            return {
                "data": [
                    {
                        "type": "campaign",
                        "id": f"CAMP{random.randint(100, 999)}",
                        "attributes": {
                            "name": f"Test Campaign {i}",
                            "status": random.choice(["draft", "sent"]),
                            "send_time": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat(),
                        },
                    }
                    for i in range(5)
                ]
            }
        if endpoint == "flows":
            return {
                "data": [
                    {
                        "type": "flow",
                        "id": f"FLOW{random.randint(100, 999)}",
                        "attributes": {
                            "name": f"Test Flow {i}",
                            "status": "live",
                            "trigger_type": "list-trigger",
                        },
                    }
                    for i in range(2)
                ]
            }
        if endpoint == "metrics":
            return {
                "data": [
                    {
                        "type": "metric",
                        "id": f"METRIC{random.randint(100, 999)}",
                        "attributes": {"name": f"Test Metric {i}"},
                    }
                    for i in range(4)
                ]
            }
        return {}
