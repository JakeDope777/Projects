'''
SEMrush Connector

Implements the ConnectorInterface for SEMrush.
Returns demo data when credentials are not configured.
'''

import logging
import random
from typing import Optional, Any, Dict
from datetime import datetime, timedelta

from .base import ConnectorInterface

logger = logging.getLogger(__name__)


class SEMrushConnector(ConnectorInterface):
    """Connector for SEMrush API."""

    BASE_URL = "https://api.semrush.com"

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(service_name="SEMrush", rate_limit=30, rate_window=60, api_key=api_key)
        if not self.api_key:
            self._enter_demo_mode()

    async def authenticate(self) -> None:
        """Authenticates with the SEMrush API using an API key."""
        if self.api_key:
            self._is_authenticated = True
            logger.info("SEMrush connector authenticated with API key.")
        else:
            self._enter_demo_mode("No API key provided.")

    async def get_data(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Fetch data from a specific API endpoint."""
        if self._demo_mode:
            return self._generate_demo_data(endpoint, params)

        await self._ensure_authenticated()
        headers = {"Accept": "application/json"}
        # SEMrush uses the key in the params
        request_params = params.copy() if params else {}
        request_params['key'] = self.api_key

        url = f"{self.BASE_URL}/{endpoint}"
        return await self._request_with_retry("GET", url, headers=headers, params=request_params)

    async def post_data(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """SEMrush API is primarily GET-based, so this is a placeholder."""
        if self._demo_mode:
            return {"status": "success", "message": "Demo mode POST acknowledged."}
        logger.warning("SEMrush connector does not support POST operations via this interface.")
        return {"error": "POST method not supported for SEMrush connector."}

    async def get_domain_overview(self, domain: str) -> Dict[str, Any]:
        """Retrieves an overview of a specified domain."""
        params = {'type': 'domain_overview', 'domain': domain}
        return await self.get_data("analytics/v1/", params=params)

    async def get_keyword_rankings(self, domain: str, keyword: str) -> Dict[str, Any]:
        """Retrieves keyword rankings for a domain."""
        params = {'type': 'domain_organic', 'domain': domain, 'display_filter': f'+|Ph|contains|{keyword}'}
        return await self.get_data("analytics/v1/", params=params)

    async def get_backlinks(self, domain: str) -> Dict[str, Any]:
        """Retrieves backlink data for a domain."""
        params = {'type': 'backlinks_overview', 'target': domain, 'target_type': 'root_domain'}
        return await self.get_data("analytics/v1/", params=params)

    async def get_organic_search(self, domain: str) -> Dict[str, Any]:
        """Retrieves organic search keywords for a domain."""
        params = {'type': 'domain_organic', 'domain': domain, 'display_limit': 10}
        return await self.get_data("analytics/v1/", params=params)

    async def get_competitors(self, domain: str) -> Dict[str, Any]:
        """Retrieves organic search competitors for a domain."""
        params = {'type': 'domain_organic_organic', 'domain': domain, 'display_limit': 10}
        return await self.get_data("analytics/v1/", params=params)

    async def get_keyword_suggestions(self, keyword: str) -> Dict[str, Any]:
        """Retrieves keyword suggestions for a given keyword."""
        params = {'type': 'phrase_related', 'phrase': keyword, 'display_limit': 10}
        return await self.get_data("analytics/v1/", params=params)

    def _generate_demo_data(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generates realistic mock data for SEMrush API endpoints."""
        if params and params.get('type') == 'domain_overview':
            return {
                "domain": params.get("domain", "example.com"),
                "organic_keywords": random.randint(1000, 50000),
                "organic_traffic": random.randint(5000, 200000),
                "adwords_keywords": random.randint(0, 5000),
                "adwords_traffic": random.randint(0, 20000),
                "backlinks": random.randint(100, 100000),
            }
        if params and params.get('type') == 'domain_organic':
            return {
                "data": [
                    {
                        "keyword": f"sample keyword {i}",
                        "position": random.randint(1, 100),
                        "traffic_share": random.uniform(0.1, 25.0),
                        "url": f"https://{params.get('domain', 'example.com')}/page-{i}"
                    } for i in range(10)
                ]
            }
        if params and params.get('type') == 'backlinks_overview':
            return {
                "total": random.randint(500, 10000),
                "domains_num": random.randint(50, 1000),
                "ips_num": random.randint(50, 500),
                "follows_num": random.randint(100, 8000),
                "nofollows_num": random.randint(100, 2000),
            }
        if params and params.get('type') == 'domain_organic_organic':
            return {
                "competitors": [
                    {
                        "domain": f"competitor{i}.com",
                        "common_keywords": random.randint(100, 5000),
                        "organic_keywords": random.randint(1000, 50000),
                    } for i in range(10)
                ]
            }
        if params and params.get('type') == 'phrase_related':
            return {
                "suggestions": [
                    {
                        "keyword": f"{params.get('phrase', 'keyword')} suggestion {i}",
                        "volume": random.randint(100, 10000),
                        "cpc": random.uniform(0.5, 10.0),
                    } for i in range(10)
                ]
            }
        return {"error": "Demo data not available for this endpoint."}
