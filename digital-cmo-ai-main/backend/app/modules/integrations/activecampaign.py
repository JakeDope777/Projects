
"""
ActiveCampaign Connector

Implements the ConnectorInterface for ActiveCampaign.
Returns demo data when credentials are not configured.
"""

import logging
import random
from typing import Optional, Any, Dict
from datetime import datetime, timedelta

from .base import ConnectorInterface, ConnectorError

logger = logging.getLogger(__name__)

class ActiveCampaignConnector(ConnectorInterface):
    """Connector for ActiveCampaign API."""

    def __init__(self, api_key: Optional[str] = None, account_url: Optional[str] = None):
        super().__init__(service_name="ActiveCampaign", rate_limit=50, rate_window=60)
        self.api_key = api_key
        self.account_url = account_url
        self.BASE_URL = f"https://{account_url}.api-us1.com/api/3" if account_url else ""

    async def authenticate(self) -> None:
        """Authenticate with the ActiveCampaign API."""
        if self.api_key and self.account_url:
            self._is_authenticated = True
            logger.info("ActiveCampaign connector authenticated.")
        else:
            self._enter_demo_mode()

    async def get_data(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Fetch data from a specific API endpoint."""
        if self._demo_mode:
            return self._generate_demo_data(endpoint, params)

        await self._ensure_authenticated()
        headers = {"Api-Token": self.api_key}
        url = f"{self.BASE_URL}/{endpoint}"
        return await self._request_with_retry("GET", url, headers=headers, params=params)

    async def post_data(self, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Send data to a specific API endpoint."""
        if self._demo_mode:
            return {"success": True, "message": "Demo mode: Data processed."}

        await self._ensure_authenticated()
        headers = {"Api-Token": self.api_key}
        url = f"{self.BASE_URL}/{endpoint}"
        return await self._request_with_retry("POST", url, headers=headers, json_data=data)

    async def get_contacts(self) -> Dict:
        """Get a list of contacts."""
        return await self.get_data("contacts")

    async def create_contact(self, email: str, first_name: str, last_name: str) -> Dict:
        """Create a new contact."""
        contact_data = {
            "contact": {
                "email": email,
                "firstName": first_name,
                "lastName": last_name,
            }
        }
        return await self.post_data("contacts", data=contact_data)

    async def get_automations(self) -> Dict:
        """Get a list of automations."""
        return await self.get_data("automations")

    async def get_campaigns(self) -> Dict:
        """Get a list of campaigns."""
        return await self.get_data("campaigns")

    async def create_campaign(self, name: str, type: str, segmentid: int) -> Dict:
        """Create a new campaign."""
        campaign_data = {
            "campaign": {
                "name": name,
                "type": type,
                "segmentid": segmentid
            }
        }
        return await self.post_data("campaigns", data=campaign_data)

    async def get_deals(self) -> Dict:
        """Get a list of deals."""
        return await self.get_data("deals")

    def _generate_demo_data(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Generate mock data for demo mode."""
        if endpoint == "contacts":
            return {
                "contacts": [
                    {
                        "id": str(random.randint(1000, 9999)),
                        "email": f"contact{i}@example.com",
                        "firstName": f"FirstName{i}",
                        "lastName": f"LastName{i}",
                    }
                    for i in range(10)
                ]
            }
        if endpoint == "automations":
            return {
                "automations": [
                    {
                        "id": str(random.randint(100, 999)),
                        "name": f"Automation {i}",
                        "status": random.choice(["active", "inactive"]),
                    }
                    for i in range(5)
                ]
            }
        if endpoint == "campaigns":
            return {
                "campaigns": [
                    {
                        "id": str(random.randint(100, 999)),
                        "name": f"Campaign {i}",
                        "type": "regular",
                        "status": "sent",
                    }
                    for i in range(5)
                ]
            }
        if endpoint == "deals":
            return {
                "deals": [
                    {
                        "id": str(random.randint(1000, 9999)),
                        "title": f"Deal {i}",
                        "value": str(random.randint(100, 10000)),
                        "currency": "USD",
                        "status": random.choice(["open", "won", "lost"]),
                    }
                    for i in range(10)
                ]
            }
        return {}
