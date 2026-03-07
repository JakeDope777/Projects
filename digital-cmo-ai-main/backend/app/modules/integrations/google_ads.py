'''
Google Ads Connector

Implements the ConnectorInterface for Google Ads.
Returns demo data when credentials are not configured.
'''

import logging
import random
from typing import Optional, Any, Dict
from datetime import datetime, timedelta

from .base import ConnectorInterface, ConnectorError

logger = logging.getLogger(__name__)


class GoogleAdsConnector(ConnectorInterface):
    """Connector for Google Ads API."""

    BASE_URL = "https://googleads.googleapis.com/v16"

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        refresh_token: Optional[str] = None,
        developer_token: Optional[str] = None,
        customer_id: Optional[str] = None,
    ):
        super().__init__(service_name="GoogleAds", rate_limit=50)
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.developer_token = developer_token
        self.customer_id = customer_id

        if not all([self.client_id, self.client_secret, self.refresh_token, self.developer_token, self.customer_id]):
            self._enter_demo_mode()

    async def authenticate(self) -> None:
        """Handles OAuth2 authentication for the Google Ads API."""
        if self._demo_mode:
            return

        # In a real scenario, you would implement the OAuth2 flow here.
        # For this example, we'll assume we have a valid access token.
        self._access_token = "dummy-access-token"  # Placeholder
        self._is_authenticated = True
        logger.info("Successfully authenticated with Google Ads.")

    async def get_data(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Fetch data from a specific API endpoint."""
        if self._demo_mode:
            return self._generate_demo_data(endpoint, params)

        await self._ensure_authenticated()
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "developer-token": self.developer_token,
            "login-customer-id": self.customer_id,
        }
        url = f"{self.BASE_URL}/{endpoint}"
        return await self._request_with_retry("GET", url, headers=headers, params=params)

    async def post_data(self, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Send data to a specific API endpoint."""
        if self._demo_mode:
            return self._generate_demo_data(endpoint, data)

        await self._ensure_authenticated()
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "developer-token": self.developer_token,
            "login-customer-id": self.customer_id,
        }
        url = f"{self.BASE_URL}/{endpoint}"
        return await self._request_with_retry("POST", url, headers=headers, json_data=data)

    async def get_campaigns(self) -> Dict:
        """Retrieves a list of campaigns."""
        endpoint = f"customers/{self.customer_id}/googleAds:search"
        query = {
            "query": "SELECT campaign.id, campaign.name, campaign.status FROM campaign ORDER BY campaign.id"
        }
        return await self.post_data(endpoint, data=query)

    async def get_campaign_metrics(self, campaign_id: Optional[str] = None) -> Dict:
        """Retrieves metrics for a specific campaign.

        In demo mode, campaign_id is optional for test and sandbox usability.
        """
        if self._demo_mode:
            campaigns = [
                {
                    "campaign_id": str(random.randint(1000, 9999)),
                    "clicks": random.randint(100, 1000),
                    "impressions": random.randint(10000, 100000),
                    "ctr": round(random.uniform(0.01, 0.1), 4),
                    "average_cpc_micros": random.randint(500000, 2000000),
                }
                for _ in range(3)
            ]
            return {"demo": True, "campaigns": campaigns}

        if campaign_id is None:
            raise ValueError("campaign_id is required outside demo mode.")

        endpoint = f"customers/{self.customer_id}/googleAds:search"
        query = {
            "query": f"SELECT metrics.clicks, metrics.impressions, metrics.ctr, metrics.average_cpc FROM campaign WHERE campaign.id = {campaign_id}"
        }
        return await self.post_data(endpoint, data=query)

    async def create_campaign(self, campaign_name: str) -> Dict:
        """Creates a new campaign."""
        endpoint = f"customers/{self.customer_id}/campaigns:mutate"
        payload = {
            "operations": [
                {
                    "create": {
                        "name": campaign_name,
                        "status": "PAUSED",
                        "advertisingChannelType": "SEARCH",
                        "biddingStrategyType": "MANUAL_CPC",
                    }
                }
            ]
        }
        return await self.post_data(endpoint, data=payload)

    async def update_campaign_budget(self, campaign_id: str, new_budget: int) -> Dict:
        """Updates the budget for a specific campaign."""
        # This is a simplified example. A real implementation would be more complex.
        endpoint = f"customers/{self.customer_id}/campaignBudgets:mutate"
        payload = {
            "operations": [
                {
                    "update": {
                        "resourceName": f"customers/{self.customer_id}/campaignBudgets/{campaign_id}",
                        "amountMicros": new_budget * 1_000_000,
                    },
                    "updateMask": "amountMicros",
                }
            ]
        }
        return await self.post_data(endpoint, data=payload)

    async def get_ad_groups(self, campaign_id: str) -> Dict:
        """Retrieves ad groups for a specific campaign."""
        endpoint = f"customers/{self.customer_id}/googleAds:search"
        query = {
            "query": f"SELECT ad_group.id, ad_group.name FROM ad_group WHERE campaign.id = {campaign_id}"
        }
        return await self.post_data(endpoint, data=query)

    async def pause_campaign(self, campaign_id: str) -> Dict:
        """Pauses a campaign."""
        endpoint = f"customers/{self.customer_id}/campaigns:mutate"
        payload = {
            "operations": [
                {
                    "update": {
                        "resourceName": f"customers/{self.customer_id}/campaigns/{campaign_id}",
                        "status": "PAUSED",
                    },
                    "updateMask": "status",
                }
            ]
        }
        return await self.post_data(endpoint, data=payload)

    def _generate_demo_data(self, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Return realistic mock data with random values."""
        if "get_campaigns" in endpoint or (data and "campaign.id" in data.get("query", "")):
            return {
                "results": [
                    {
                        "campaign": {
                            "resourceName": f"customers/{self.customer_id}/campaigns/{random.randint(1000, 9999)}",
                            "id": str(random.randint(1000, 9999)),
                            "name": f"Demo Campaign {i}",
                            "status": random.choice(["ENABLED", "PAUSED", "REMOVED"]),
                        }
                    }
                    for i in range(1, random.randint(3, 7))
                ]
            }
        if "get_campaign_metrics" in endpoint or (data and "metrics.clicks" in data.get("query", "")):
            return {
                "results": [
                    {
                        "metrics": {
                            "clicks": str(random.randint(100, 1000)),
                            "impressions": str(random.randint(10000, 100000)),
                            "ctr": random.uniform(0.01, 0.1),
                            "averageCpc": str(random.randint(500000, 2000000)),
                        }
                    }
                ]
            }
        if "create_campaign" in endpoint or (data and "create" in data.get("operations", [{}])[0]):
            return {"results": [{"resourceName": f"customers/{self.customer_id}/campaigns/{random.randint(1000, 9999)}"}]}
        if "update_campaign_budget" in endpoint or (data and "update" in data.get("operations", [{}])[0]):
            return {"results": [{"resourceName": f"customers/{self.customer_id}/campaignBudgets/{random.randint(1000, 9999)}"}]}
        if "get_ad_groups" in endpoint or (data and "ad_group.id" in data.get("query", "")):
            return {
                "results": [
                    {
                        "adGroup": {
                            "resourceName": f"customers/{self.customer_id}/adGroups/{random.randint(10000, 99999)}",
                            "id": str(random.randint(10000, 99999)),
                            "name": f"Demo Ad Group {i}",
                        }
                    }
                    for i in range(1, random.randint(2, 5))
                ]
            }
        if "pause_campaign" in endpoint or (data and "PAUSED" in str(data)):
            return {"results": [{"resourceName": f"customers/{self.customer_id}/campaigns/{random.randint(1000, 9999)}"}]}

        return {}
