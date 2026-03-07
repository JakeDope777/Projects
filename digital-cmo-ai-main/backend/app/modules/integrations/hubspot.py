'''
HubSpot Connector

Implements the ConnectorInterface for HubSpot.
Returns demo data when credentials are not configured.
'''

import logging
import random
from typing import Optional, Any, Dict
from datetime import datetime, timedelta

from .base import ConnectorInterface, ConnectorError

logger = logging.getLogger(__name__)


class HubSpotConnector(ConnectorInterface):
    """Connector for HubSpot API."""

    BASE_URL = "https://api.hubapi.com"

    def __init__(self, api_key: Optional[str] = None, access_token: Optional[str] = None):
        super().__init__(service_name="HubSpot", rate_limit=100, rate_window=60)
        self.api_key = api_key
        self.access_token = access_token
        if not self.api_key and not self.access_token:
            self._enter_demo_mode()

    async def authenticate(self) -> None:
        """Authenticate with HubSpot using API key or OAuth2 access token."""
        if self._demo_mode:
            return

        if self.api_key:
            self._is_authenticated = True
            logger.info("[HubSpot] Authenticated using API key.")
        elif self.access_token:
            self._is_authenticated = True
            logger.info("[HubSpot] Authenticated using OAuth2 access token.")
        else:
            self._enter_demo_mode("No API key or access token provided.")

    async def get_data(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """Fetch data from a specific HubSpot API endpoint."""
        if self._demo_mode:
            return self._generate_demo_data(endpoint, params)

        await self._ensure_authenticated()
        headers = self._get_auth_headers()
        url = f"{self.BASE_URL}{endpoint}"
        return await self._request_with_retry("GET", url, headers=headers, params=params)

    async def post_data(self, endpoint: str, data: Optional[dict] = None) -> dict:
        """Send data to a specific HubSpot API endpoint."""
        if self._demo_mode:
            return {"status": "success", "message": "Demo mode: Data processed."}

        await self._ensure_authenticated()
        headers = self._get_auth_headers()
        url = f"{self.BASE_URL}{endpoint}"
        return await self._request_with_retry("POST", url, headers=headers, json_data=data)

    async def patch_data(self, endpoint: str, data: Optional[dict] = None) -> dict:
        """Update data at a specific HubSpot API endpoint."""
        if self._demo_mode:
            return {"status": "success", "message": "Demo mode: Data updated."}

        await self._ensure_authenticated()
        headers = self._get_auth_headers()
        url = f"{self.BASE_URL}{endpoint}"
        return await self._request_with_retry("PATCH", url, headers=headers, json_data=data)

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers."""
        if self.api_key:
            return {"Authorization": f"Bearer {self.api_key}"}
        elif self.access_token:
            return {"Authorization": f"Bearer {self.access_token}"}
        return {}

    async def get_contacts(self, limit: int = 10) -> dict:
        """Retrieve a list of contacts."""
        return await self.get_data("/crm/v3/objects/contacts", params={"limit": limit})

    async def create_contact(self, properties: dict) -> dict:
        """Create a new contact."""
        return await self.post_data("/crm/v3/objects/contacts", data={"properties": properties})

    async def get_deals(self, limit: int = 10) -> dict:
        """Retrieve a list of deals."""
        return await self.get_data("/crm/v3/objects/deals", params={"limit": limit})

    async def create_deal(self, properties: dict) -> dict:
        """Create a new deal."""
        return await self.post_data("/crm/v3/objects/deals", data={"properties": properties})

    async def get_companies(self, limit: int = 10) -> dict:
        """Retrieve a list of companies."""
        return await self.get_data("/crm/v3/objects/companies", params={"limit": limit})

    async def update_contact(self, contact_id: str, properties: dict) -> dict:
        """Update an existing contact."""
        return await self.patch_data(f"/crm/v3/objects/contacts/{contact_id}", data={"properties": properties})

    def _generate_demo_data(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """Generate realistic mock data for HubSpot endpoints."""
        params = params or {}
        if "contacts" in endpoint:
            return {
                "demo": True,
                "results": [
                    {
                        "id": str(random.randint(1000, 9999)),
                        "properties": {
                            "createdate": (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat(),
                            "email": f"contact{i}@example.com",
                            "firstname": f"FirstName{i}",
                            "lastname": f"LastName{i}",
                        },
                    }
                    for i in range(params.get("limit", 10))
                ]
            }
        if "deals" in endpoint:
            return {
                "demo": True,
                "results": [
                    {
                        "id": str(random.randint(1000, 9999)),
                        "properties": {
                            "dealname": f"Demo Deal {i}",
                            "amount": str(random.uniform(100, 10000)),
                            "dealstage": random.choice(["appointmentscheduled", "qualifiedtobuy", "presentationscheduled"]),
                        },
                    }
                    for i in range(params.get("limit", 10))
                ]
            }
        if "companies" in endpoint:
            return {
                "demo": True,
                "results": [
                    {
                        "id": str(random.randint(1000, 9999)),
                        "properties": {
                            "name": f"Demo Company {i}",
                            "domain": f"democompany{i}.com",
                            "city": "Demo City",
                        },
                    }
                    for i in range(params.get("limit", 10))
                ]
            }
        return {"demo": True}
