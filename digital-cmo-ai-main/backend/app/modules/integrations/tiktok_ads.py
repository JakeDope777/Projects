'''
Tiktok Ads Connector

Implements the ConnectorInterface for Tiktok Ads.
Returns demo data when credentials are not configured.
'''

import logging
import random
from typing import Optional, Any, Dict
from datetime import datetime, timedelta

from .base import ConnectorInterface, ConnectorError

logger = logging.getLogger(__name__)


class TikTokAdsConnector(ConnectorInterface):
    """Connector for Tiktok Ads API."""

    BASE_URL = "https://business-api.tiktok.com/open_api/v1.3"

    def __init__(self, advertiser_id: str, access_token: Optional[str] = None):
        super().__init__(service_name="TikTokAds", rate_limit=50, rate_window=60)
        self.advertiser_id = advertiser_id
        self._access_token = access_token
        if not self._access_token:
            self._enter_demo_mode()

    async def authenticate(self) -> None:
        """Checks if an access token is present."""
        if self._access_token:
            self._is_authenticated = True
            logger.info(f"[{self.service_name}] Authenticated using provided access token.")
        else:
            self._is_authenticated = False
            logger.warning(f"[{self.service_name}] No access token provided.")

    async def get_data(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Fetch data from a specific API endpoint."""
        if self._demo_mode:
            return self._generate_demo_data(endpoint, params)

        await self._ensure_authenticated()
        headers = {"Access-Token": self._access_token}
        url = f"{self.BASE_URL}{endpoint}"
        return await self._request_with_retry("GET", url, headers=headers, params=params)

    async def post_data(self, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Send data to a specific API endpoint."""
        if self._demo_mode:
            return self._generate_demo_data(endpoint, data)

        await self._ensure_authenticated()
        headers = {"Access-Token": self._access_token}
        url = f"{self.BASE_URL}{endpoint}"
        return await self._request_with_retry("POST", url, headers=headers, json_data=data)

    async def get_campaigns(self, params: Optional[Dict] = None) -> Dict:
        """Retrieves a list of campaigns."""
        endpoint = "/campaign/get/"
        final_params = {"advertiser_id": self.advertiser_id}
        if params: 
            final_params.update(params)
        return await self.get_data(endpoint, params=final_params)

    async def get_ad_groups(self, campaign_id: str, params: Optional[Dict] = None) -> Dict:
        """Retrieves ad groups for a given campaign."""
        endpoint = "/adgroup/get/"
        final_params = {"advertiser_id": self.advertiser_id, "campaign_id": campaign_id}
        if params: 
            final_params.update(params)
        return await self.get_data(endpoint, params=final_params)

    async def get_ad_metrics(self, ad_ids: list[str], metrics: list[str]) -> Dict:
        """Retrieves metrics for a list of ads."""
        endpoint = "/report/integrated/get/"
        params = {
            "advertiser_id": self.advertiser_id,
            "report_type": "BASIC",
            "dimensions": ["ad_id"],
            "metrics": metrics,
            "data_level": "AUCTION_AD",
            "filter": [{"field_name": "ad_id", "filter_type": "IN", "filter_value": ad_ids}]
        }
        return await self.get_data(endpoint, params=params)

    async def create_campaign(self, campaign_data: Dict) -> Dict:
        """Creates a new campaign."""
        endpoint = "/campaign/create/"
        campaign_data["advertiser_id"] = self.advertiser_id
        return await self.post_data(endpoint, data=campaign_data)

    async def update_campaign_status(self, campaign_id: str, status: str) -> Dict:
        """Updates the status of a campaign."""
        endpoint = "/campaign/update/status/"
        data = {
            "advertiser_id": self.advertiser_id,
            "campaign_ids": [campaign_id],
            "operation_status": status
        }
        return await self.post_data(endpoint, data=data)

    async def get_audience_report(self, adgroup_id: str, start_date: str, end_date: str) -> Dict:
        """Retrieves an audience report for an ad group."""
        endpoint = "/report/audience/get/"
        params = {
            "advertiser_id": self.advertiser_id,
            "adgroup_id": adgroup_id,
            "start_date": start_date,
            "end_date": end_date
        }
        return await self.get_data(endpoint, params=params)

    def _generate_demo_data(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Generates mock data for the TikTok Ads API."""
        if endpoint == "/campaign/get/":
            return {
                "code": 0,
                "message": "OK",
                "data": {
                    "list": [
                        {
                            "campaign_id": str(random.randint(1000000000, 9999999999)),
                            "campaign_name": f"Demo Campaign {random.randint(1, 100)}",
                            "status": random.choice(["CAMPAIGN_STATUS_ENABLE", "CAMPAIGN_STATUS_DISABLE"]),
                            "budget": random.uniform(100, 1000)
                        } for _ in range(5)
                    ]
                }
            }
        if endpoint == "/adgroup/get/":
            return {
                "code": 0,
                "message": "OK",
                "data": {
                    "list": [
                        {
                            "adgroup_id": str(random.randint(1000000000, 9999999999)),
                            "adgroup_name": f"Demo Ad Group {random.randint(1, 100)}",
                            "status": random.choice(["ADGROUP_STATUS_ENABLE", "ADGROUP_STATUS_DISABLE"]),
                        } for _ in range(3)
                    ]
                }
            }
        if endpoint == "/report/integrated/get/":
            return {
                "code": 0,
                "message": "OK",
                "data": {
                    "list": [
                        {
                            "metrics": {
                                "impressions": random.randint(1000, 10000),
                                "clicks": random.randint(100, 1000),
                                "spend": random.uniform(50, 500)
                            },
                            "dimensions": {
                                "ad_id": params.get("filter")[0].get("filter_value")[0]
                            }
                        }
                    ]
                }
            }
        if endpoint == "/campaign/create/":
            return {
                "code": 0,
                "message": "OK",
                "data": {
                    "campaign_id": str(random.randint(1000000000, 9999999999))
                }
            }
        if endpoint == "/campaign/update/status/":
            return {
                "code": 0,
                "message": "OK"
            }
        if endpoint == "/report/audience/get/":
            return {
                "code": 0,
                "message": "OK",
                "data": {
                    "list": [
                        {
                            "metrics": {
                                "age": f"{random.randint(18, 65)}",
                                "gender": random.choice(["MALE", "FEMALE"]),
                                "impressions": random.randint(500, 5000)
                            }
                        }
                    ]
                }
            }
        return {}
