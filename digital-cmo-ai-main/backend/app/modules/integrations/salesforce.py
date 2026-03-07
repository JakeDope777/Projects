
"""
Salesforce Connector

Implements the ConnectorInterface for Salesforce.
Returns demo data when credentials are not configured.
"""

import logging
import random
from typing import Optional, Any, Dict, List
from datetime import datetime, timedelta

from .base import ConnectorInterface, ConnectorError

logger = logging.getLogger(__name__)


class SalesforceConnector(ConnectorInterface):
    """Connector for Salesforce API."""

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        instance_url: Optional[str] = None,
        refresh_token: Optional[str] = None,
    ):
        super().__init__(service_name="Salesforce", rate_limit=50)
        self.client_id = client_id
        self.client_secret = client_secret
        self.instance_url = instance_url
        self.refresh_token = refresh_token
        self._base_url = f"{self.instance_url}/services/data/v59.0" if self.instance_url else ""

        if not all([self.client_id, self.client_secret, self.instance_url, self.refresh_token]):
            self._enter_demo_mode()

    async def authenticate(self) -> None:
        """Authenticate with Salesforce using OAuth2."""
        if self._demo_mode:
            logger.info("Salesforce connector is in demo mode. Skipping authentication.")
            return

        if self.is_token_expired():
            await self.refresh_access_token()
        else:
            self._is_authenticated = True
            logger.info("Salesforce access token is still valid.")

    async def refresh_access_token(self) -> None:
        """Refresh the OAuth2 access token."""
        if self._demo_mode:
            return

        token_url = f"https://{self.instance_url.split('//')[1]}/services/oauth2/token"
        payload = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
        }
        
        import aiohttp
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(token_url, data=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self._access_token = data["access_token"]
                        # Salesforce refresh tokens don't expire but can be revoked.
                        # We will assume the token is valid for 1 hour for simplicity.
                        self._token_expires_at = datetime.now().timestamp() + 3600
                        self._is_authenticated = True
                        logger.info("Salesforce access token refreshed successfully.")
                    else:
                        error_text = await resp.text()
                        self._enter_demo_mode(f"Failed to refresh token: {error_text}")
                        raise ConnectorError("Salesforce", resp.status, error_text, "AUTH_ERROR")
        except aiohttp.ClientError as e:
            self._enter_demo_mode(f"HTTP error during token refresh: {e}")
            raise ConnectorError("Salesforce", 0, str(e), "NETWORK_ERROR")

    async def get_data(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Fetch data from a Salesforce API endpoint."""
        if self._demo_mode:
            return self._generate_demo_data(endpoint, params)

        await self._ensure_authenticated()
        headers = {"Authorization": f"Bearer {self._access_token}"}
        url = f"{self._base_url}{endpoint}"
        return await self._request_with_retry("GET", url, headers=headers, params=params)

    async def post_data(self, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Send data to a Salesforce API endpoint."""
        if self._demo_mode:
            return self._generate_demo_data(endpoint, data)

        await self._ensure_authenticated()
        headers = {"Authorization": f"Bearer {self._access_token}"}
        url = f"{self._base_url}{endpoint}"
        return await self._request_with_retry("POST", url, headers=headers, json_data=data)

    async def get_contacts(self, limit: int = 10) -> Dict:
        """Retrieve a list of contacts."""
        return await self.get_data("/query", params={"q": f"SELECT Id, Name, Email, Phone, Title FROM Contact LIMIT {limit}"})

    async def create_lead(self, lead_data: Dict) -> Dict:
        """Create a new lead."""
        return await self.post_data("/sobjects/Lead", data=lead_data)

    async def get_opportunities(self, stage: str = 'Prospecting', limit: int = 10) -> Dict:
        """Retrieve a list of opportunities."""
        return await self.get_data("/query", params={"q": f"SELECT Id, Name, StageName, Amount, CloseDate FROM Opportunity WHERE StageName = '{stage}' LIMIT {limit}"})

    async def update_opportunity(self, opportunity_id: str, update_data: Dict) -> Dict:
        """Update an existing opportunity."""
        return await self._request_with_retry("PATCH", f"{self._base_url}/sobjects/Opportunity/{opportunity_id}", headers={"Authorization": f"Bearer {self._access_token}"}, json_data=update_data)

    async def run_soql_query(self, query: str) -> Dict:
        """Run a raw SOQL query."""
        return await self.get_data("/query", params={"q": query})

    async def get_account(self, account_id: str) -> Dict:
        """Get details for a specific account."""
        return await self.get_data(f"/sobjects/Account/{account_id}")

    def _generate_demo_data(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Generate mock data for Salesforce endpoints."""
        if "query" in endpoint:
            if "Contact" in params.get("q", ""):
                return {"totalSize": 2, "done": True, "records": [
                    {"attributes": {"type": "Contact"}, "Id": "0038d00000ABCDE", "Name": "John Doe", "Email": "john.doe@example.com", "Phone": "123-456-7890", "Title": "CEO"},
                    {"attributes": {"type": "Contact"}, "Id": "0038d00000FGHIJ", "Name": "Jane Smith", "Email": "jane.smith@example.com", "Phone": "098-765-4321", "Title": "CTO"}
                ]}
            if "Opportunity" in params.get("q", ""):
                return {"totalSize": 1, "done": True, "records": [
                    {"attributes": {"type": "Opportunity"}, "Id": "0068d00000KLMNO", "Name": "Big Deal", "StageName": "Prospecting", "Amount": 100000.0, "CloseDate": (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')}
                ]}
            return {"totalSize": 0, "done": True, "records": []}
        if "Lead" in endpoint:
            return {"id": f"00Q8d00000{random.randint(10000, 99999)}", "success": True, "errors": []}
        if "Account" in endpoint:
            return {"attributes": {"type": "Account"}, "Id": "0018d00000PQRST", "Name": "Demo Account Inc.", "BillingStreet": "123 Demo St", "BillingCity": "Demo City"}
        if "Opportunity" in endpoint:
            return {"id": params.get("opportunity_id", "0068d00000KLMNO"), "success": True, "errors": []}

        return {}
