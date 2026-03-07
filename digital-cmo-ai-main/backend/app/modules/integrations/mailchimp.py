'''
Mailchimp Connector

Implements the ConnectorInterface for Mailchimp.
Returns demo data when credentials are not configured.
'''

import logging
import random
from typing import Optional, Any
from datetime import datetime, timedelta

from .base import ConnectorInterface

logger = logging.getLogger(__name__)


class MailchimpConnector(ConnectorInterface):
    """Connector for Mailchimp API."""

    def __init__(self, api_key: Optional[str] = None, dc: Optional[str] = None):
        super().__init__(service_name="Mailchimp", rate_limit=60, rate_window=60)
        self.api_key = api_key
        self.dc = dc
        self.BASE_URL = f"https://{self.dc}.api.mailchimp.com/3.0" if self.dc else ""

        if not self.api_key or not self.dc:
            self._enter_demo_mode()

    async def authenticate(self) -> None:
        """Set up authentication headers."""
        if self.demo_mode:
            return

        if not self.api_key:
            raise ValueError("API key is required for Mailchimp authentication.")

        self._headers = {
            "Authorization": f"apikey {self.api_key}",
            "Content-Type": "application/json",
        }
        self._is_authenticated = True
        logger.info("Mailchimp connector authenticated successfully.")

    async def get_data(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """Fetch data from a specific API endpoint."""
        if self.demo_mode:
            return self._generate_demo_data(endpoint, params)

        await self._ensure_authenticated()
        url = f"{self.BASE_URL}/{endpoint}"
        return await self._request_with_retry(
            "GET", url, headers=self._headers, params=params
        )

    async def post_data(self, endpoint: str, data: Optional[dict] = None) -> dict:
        """Send data to a specific API endpoint."""
        if self.demo_mode:
            return {"status": "success", "id": random.randint(1000, 9999)}

        await self._ensure_authenticated()
        url = f"{self.BASE_URL}/{endpoint}"
        return await self._request_with_retry(
            "POST", url, headers=self._headers, json_data=data
        )

    async def get_lists(self) -> dict:
        """Get all mailing lists."""
        return await self.get_data("lists")

    async def get_campaigns(self) -> dict:
        """Get all campaigns."""
        return await self.get_data("campaigns")

    async def create_campaign(self, list_id: str, subject: str, from_name: str, reply_to: str) -> dict:
        """Create a new campaign."""
        data = {
            "type": "regular",
            "recipients": {"list_id": list_id},
            "settings": {
                "subject_line": subject,
                "from_name": from_name,
                "reply_to": reply_to,
            },
        }
        return await self.post_data("campaigns", data)

    async def send_campaign(self, campaign_id: str) -> dict:
        """Send a campaign."""
        return await self.post_data(f"campaigns/{campaign_id}/actions/send")

    async def get_campaign_report(self, campaign_id: str) -> dict:
        """Get a report for a campaign."""
        return await self.get_data(f"reports/{campaign_id}")

    async def add_subscriber(self, list_id: str, email_address: str, status: str = "subscribed") -> dict:
        """Add a new subscriber to a list."""
        data = {
            "email_address": email_address,
            "status": status,
        }
        return await self.post_data(f"lists/{list_id}/members", data)

    def _generate_demo_data(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """Return realistic mock data with random values."""
        if endpoint == "lists":
            return {
                "lists": [
                    {
                        "id": f"l_{random.randint(100, 999)}",
                        "name": f"Demo List {i}",
                        "stats": {"member_count": random.randint(50, 1000)},
                    }
                    for i in range(1, 4)
                ]
            }
        if endpoint == "campaigns":
            return {
                "campaigns": [
                    {
                        "id": f"c_{random.randint(100, 999)}",
                        "type": "regular",
                        "status": random.choice(["sent", "draft"]),
                        "send_time": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat(),
                        "subject_line": f"Demo Campaign {i}",
                    }
                    for i in range(1, 6)
                ]
            }
        if endpoint.startswith("reports/"):
            return {
                "id": endpoint.split("/")[1],
                "opens": {"opens_total": random.randint(100, 500)},
                "clicks": {"clicks_total": random.randint(10, 100)},
                "bounces": {"hard_bounces": random.randint(1, 10), "soft_bounces": random.randint(5, 20)},
            }
        return {}
