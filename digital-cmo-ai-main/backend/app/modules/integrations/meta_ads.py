
"""
Meta/Facebook Ads Connector

Implements the ConnectorInterface for Meta/Facebook Ads.
Returns demo data when credentials are not configured.
"""

import logging
import random
from typing import Optional, Any, Dict
from datetime import datetime, timedelta

from .base import ConnectorInterface, ConnectorError

logger = logging.getLogger(__name__)


class MetaAdsConnector(ConnectorInterface):
    """Connector for Meta/Facebook Ads API."""

    BASE_URL = "https://graph.facebook.com/v19.0"

    def __init__(self, access_token: Optional[str] = None, ad_account_id: Optional[str] = None):
        super().__init__(service_name="MetaAds", rate_limit=60)
        self.access_token = access_token
        self.ad_account_id = ad_account_id
        if not self.access_token or not self.ad_account_id:
            self._enter_demo_mode("Missing access token or ad account ID")

    async def authenticate(self) -> None:
        """Authenticates the connector."""
        if self._demo_mode:
            return

        if not self.access_token:
            self._enter_demo_mode("No access token provided.")
            return

        # For Meta Ads, the access token is the authentication.
        # We can make a test call to verify it.
        try:
            await self.get_data(f"act_{self.ad_account_id}", {"fields": "id"})
            self._is_authenticated = True
            logger.info("MetaAds connector authenticated successfully.")
        except ConnectorError as e:
            self._is_authenticated = False
            logger.error(f"MetaAds authentication failed: {e}")
            raise

    async def get_data(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Fetch data from a specific API endpoint."""
        if self._demo_mode:
            return self._generate_demo_data(endpoint, params)

        await self._ensure_authenticated()
        headers = {"Authorization": f"Bearer {self.access_token}"}
        url = f"{self.BASE_URL}/{endpoint}"
        return await self._request_with_retry("GET", url, headers=headers, params=params)

    async def post_data(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send data to a specific API endpoint."""
        if self._demo_mode:
            return self._generate_demo_data(endpoint, data)

        await self._ensure_authenticated()
        headers = {"Authorization": f"Bearer {self.access_token}"}
        url = f"{self.BASE_URL}/{endpoint}"
        return await self._request_with_retry("POST", url, headers=headers, json_data=data)

    async def get_campaigns(self) -> Dict[str, Any]:
        """Retrieves a list of ad campaigns."""
        return await self.get_data(f"act_{self.ad_account_id}/campaigns", {"fields": "id,name,status,objective"})

    async def get_ad_sets(self, campaign_id: str) -> Dict[str, Any]:
        """Retrieves ad sets for a given campaign."""
        return await self.get_data(f"{campaign_id}/adsets", {"fields": "id,name,status,daily_budget"})

    async def get_ad_metrics(self, ad_id: str) -> Dict[str, Any]:
        """Retrieves metrics for a specific ad."""
        return await self.get_data(f"{ad_id}/insights", {"fields": "impressions,clicks,spend,cpc,ctr"})

    async def create_campaign(self, name: str, objective: str) -> Dict[str, Any]:
        """Creates a new ad campaign."""
        data = {
            "name": name,
            "objective": objective,
            "status": "PAUSED",
            "special_ad_categories": []
        }
        return await self.post_data(f"act_{self.ad_account_id}/campaigns", data)

    async def update_ad_set(self, ad_set_id: str, new_name: str) -> Dict[str, Any]:
        """Updates an existing ad set."""
        data = {"name": new_name}
        return await self.post_data(ad_set_id, data)

    async def get_audience_insights(self) -> Dict[str, Any]:
        """Retrieves audience insights."""
        # This is a simplified representation. Real audience insights are more complex.
        return await self.get_data(f"act_{self.ad_account_id}/delivery_estimate")

    def _generate_demo_data(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generates realistic mock data for demo mode."""
        if "campaigns" in endpoint:
            return {
                "data": [
                    {
                        "id": f"v_campaign_{random.randint(1000, 9999)}",
                        "name": f"Demo Campaign {i}",
                        "status": random.choice(["ACTIVE", "PAUSED", "ARCHIVED"]),
                        "objective": random.choice(["LINK_CLICKS", "CONVERSIONS", "POST_ENGAGEMENT"])
                    } for i in range(5)
                ]
            }
        if "adsets" in endpoint:
            return {
                "data": [
                    {
                        "id": f"v_adset_{random.randint(1000, 9999)}",
                        "name": f"Demo Ad Set {i}",
                        "status": random.choice(["ACTIVE", "PAUSED", "ARCHIVED"]),
                        "daily_budget": str(random.randint(1000, 5000))
                    } for i in range(3)
                ]
            }
        if "insights" in endpoint:
            return {
                "data": [
                    {
                        "impressions": str(random.randint(10000, 50000)),
                        "clicks": str(random.randint(500, 2000)),
                        "spend": f"{random.uniform(100, 500):.2f}",
                        "cpc": f"{random.uniform(0.5, 2.5):.2f}",
                        "ctr": f"{random.uniform(1, 5):.2f}"
                    }
                ]
            }
        if "delivery_estimate" in endpoint:
            return {
                "data": [
                    {
                        "daily_outcomes_curve": {
                            "data_points": [
                                {
                                    "spend": 100,
                                    "reach": random.randint(10000, 20000),
                                    "impressions": random.randint(15000, 30000),
                                    "actions": random.randint(50, 150)
                                },
                                {
                                    "spend": 200,
                                    "reach": random.randint(20000, 40000),
                                    "impressions": random.randint(30000, 60000),
                                    "actions": random.randint(100, 300)
                                }
                            ]
                        }
                    }
                ]
            }
        if "campaigns" in endpoint and params and "name" in params:
            return {"id": f"v_campaign_{random.randint(1000, 9999)}"}
        if params and "name" in params:
            return {"success": True}

        return {}
