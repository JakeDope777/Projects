'''
Zoho CRM Connector

Implements the ConnectorInterface for Zoho CRM.
Returns demo data when credentials are not configured.
'''

import logging
import random
from typing import Optional, Any, Dict
from datetime import datetime, timedelta

from .base import ConnectorInterface, ConnectorError

logger = logging.getLogger(__name__)


class ZohoCRMConnector(ConnectorInterface):
    """Connector for Zoho CRM API."""

    BASE_URL = "https://www.zohoapis.com/crm/v5"

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        refresh_token: Optional[str] = None,
    ):
        super().__init__(service_name="ZohoCRM", rate_limit=60)
        self.client_id = client_id
        self.client_secret = client_secret
        self._refresh_token = refresh_token
        self._access_token: Optional[str] = None

        if not all([self.client_id, self.client_secret, self._refresh_token]):
            self._enter_demo_mode("Missing OAuth2 credentials.")

    async def authenticate(self) -> None:
        """Refreshes the access token using the refresh token."""
        if self._demo_mode:
            return

        if not self.client_id or not self.client_secret or not self._refresh_token:
            self._enter_demo_mode("Cannot authenticate without credentials.")
            return

        token_url = "https://accounts.zoho.com/oauth/v2/token"
        payload = {
            "refresh_token": self._refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
        }
        try:
            # Use a temporary aiohttp session for authentication
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(token_url, data=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self._access_token = data["access_token"]
                        self._is_authenticated = True
                        logger.info("Zoho CRM authentication successful.")
                    else:
                        error_text = await resp.text()
                        raise ConnectorError(
                            "ZohoCrm", resp.status, f"Failed to refresh token: {error_text}"
                        )
        except Exception as e:
            logger.error(f"Error during Zoho CRM authentication: {e}")
            self._enter_demo_mode("Authentication failed.")

    async def get_data(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Fetch data from a specific API endpoint."""
        if self._demo_mode:
            return self._generate_demo_data(endpoint, params)

        await self._ensure_authenticated()
        url = f"{self.BASE_URL}/{endpoint}"
        headers = {"Authorization": f"Zoho-oauthtoken {self._access_token}"}
        return await self._request_with_retry("GET", url, headers=headers, params=params)

    async def post_data(self, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Send data to a specific API endpoint."""
        if self._demo_mode:
            return {"status": "success", "message": "Demo mode: Data not sent."}

        await self._ensure_authenticated()
        url = f"{self.BASE_URL}/{endpoint}"
        headers = {"Authorization": f"Zoho-oauthtoken {self._access_token}"}
        return await self._request_with_retry("POST", url, headers=headers, json_data=data)

    async def get_leads(self, count: int = 10) -> Dict:
        """Get a list of leads."""
        return await self.get_data("Leads", params={"per_page": count})

    async def create_lead(self, lead_data: Dict) -> Dict:
        """Create a new lead."""
        return await self.post_data("Leads", data={"data": [lead_data]})

    async def get_contacts(self, count: int = 10) -> Dict:
        """Get a list of contacts."""
        return await self.get_data("Contacts", params={"per_page": count})

    async def get_deals(self, count: int = 10) -> Dict:
        """Get a list of deals."""
        return await self.get_data("Deals", params={"per_page": count})

    async def update_deal(self, deal_id: str, deal_data: Dict) -> Dict:
        """Update an existing deal."""
        return await self._request_with_retry(
            "PUT", f"{self.BASE_URL}/Deals/{deal_id}",
            headers={"Authorization": f"Zoho-oauthtoken {self._access_token}"},
            json_data={"data": [deal_data]}
        )

    async def search_records(self, module: str, criteria: str) -> Dict:
        """Search for records in a specific module."""
        return await self.get_data(f"{module}/search", params={"criteria": criteria})

    def _generate_demo_data(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Return realistic mock data with random values."""
        if endpoint == "Leads":
            return {
                "data": [
                    {
                        "id": str(random.randint(10000, 99999)),
                        "Company": f"Corp {random.randint(1, 100)}",
                        "Last_Name": f"User {random.randint(1, 100)}",
                        "First_Name": "Test",
                        "Email": f"test.user{random.randint(1,100)}@example.com",
                        "Lead_Status": random.choice(["Contacted", "Not Contacted", "Lost Lead"]),
                    }
                    for _ in range(params.get("per_page", 10))
                ]
            }
        if endpoint == "Contacts":
            return {
                "data": [
                    {
                        "id": str(random.randint(10000, 99999)),
                        "Last_Name": f"Contact {random.randint(1, 100)}",
                        "First_Name": "Demo",
                        "Email": f"demo.contact{random.randint(1,100)}@example.com",
                    }
                    for _ in range(params.get("per_page", 10))
                ]
            }
        if endpoint == "Deals":
            return {
                "data": [
                    {
                        "id": str(random.randint(10000, 99999)),
                        "Deal_Name": f"Deal {random.randint(1, 100)}",
                        "Stage": random.choice(["Qualification", "Proposal", "Closed Won", "Closed Lost"]),
                        "Amount": round(random.uniform(1000, 50000), 2),
                    }
                    for _ in range(params.get("per_page", 10))
                ]
            }
        return {}
