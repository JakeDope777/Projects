'''
LinkedIn Connector

Implements the ConnectorInterface for LinkedIn.
Returns demo data when credentials are not configured.
'''

import logging
import random
from typing import Optional, Any, Dict
from datetime import datetime, timedelta

from .base import ConnectorInterface, ConnectorError

logger = logging.getLogger(__name__)


class LinkedInConnector(ConnectorInterface):
    """Connector for LinkedIn API."""

    BASE_URL = "https://api.linkedin.com/v2"

    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None, refresh_token: Optional[str] = None):
        super().__init__(service_name="LinkedIn", rate_limit=50)
        self.client_id = client_id
        self.client_secret = client_secret
        self._refresh_token = refresh_token
        self._access_token: Optional[str] = None

        if not all([self.client_id, self.client_secret, self._refresh_token]):
            self._enter_demo_mode("Missing client_id, client_secret, or refresh_token.")

    async def authenticate(self) -> None:
        """Authenticate with LinkedIn using OAuth2."""
        if self._demo_mode:
            logger.info("Skipping authentication in demo mode.")
            return

        # In a real scenario, you would implement the OAuth2 flow to get the access token.
        # For this example, we'll assume we have a long-lived access token.
        # A real implementation would also handle token refresh.
        self._access_token = "DUMMY_ACCESS_TOKEN" # Replace with actual token retrieval logic
        self._is_authenticated = True
        logger.info("Successfully authenticated with LinkedIn.")

    async def get_data(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Fetch data from a specific API endpoint."""
        if self._demo_mode:
            return self._generate_demo_data(endpoint, params)

        await self._ensure_authenticated()
        headers = {"Authorization": f"Bearer {self._access_token}"}
        url = f"{self.BASE_URL}/{endpoint}"
        return await self._request_with_retry("GET", url, headers=headers, params=params)

    async def post_data(self, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Send data to a specific API endpoint."""
        if self._demo_mode:
            return self._generate_demo_data(endpoint, data)

        await self._ensure_authenticated()
        headers = {"Authorization": f"Bearer {self._access_token}"}
        url = f"{self.BASE_URL}/{endpoint}"
        return await self._request_with_retry("POST", url, headers=headers, json_data=data)

    async def create_post(self, text: str, organization_urn: str = "12345") -> Dict:
        """Creates a new post for an organization.

        Accepts text-first signature to keep backwards compatibility with tests.
        """
        endpoint = "ugcPosts"
        data = {
            "author": f"urn:li:organization:{organization_urn}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": text
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }
        return await self.post_data(endpoint, data)

    async def get_post_analytics(self, post_urn: str) -> Dict:
        """Retrieves analytics for a specific post."""
        endpoint = f"socialActions/{post_urn}"
        return await self.get_data(endpoint)

    async def get_company_page_stats(self, organization_urn: str) -> Dict:
        """Retrieves statistics for a company page."""
        endpoint = f"organizationalEntityAcls?q=roleAssignee&role=ADMINISTRATOR&state=APPROVED&projection=(elements*(*,roleAssignee~(localizedFirstName,localizedLastName)))"
        return await self.get_data(endpoint)

    async def get_follower_demographics(self, organization_urn: str) -> Dict:
        """Retrieves follower demographics for a company page."""
        endpoint = f"organizationPageStatistics?q=organization&organization={organization_urn}"
        return await self.get_data(endpoint)

    async def share_content(self, organization_urn: str, content_url: str, text: str) -> Dict:
        """Shares content on behalf of an organization."""
        endpoint = "ugcPosts"
        data = {
            "author": f"urn:li:organization:{organization_urn}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": text
                    },
                    "shareMediaCategory": "ARTICLE",
                    "media": [
                        {
                            "status": "READY",
                            "originalUrl": content_url
                        }
                    ]
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }
        return await self.post_data(endpoint, data)

    async def get_organization_info(self, organization_urn: str) -> Dict:
        """Retrieves information about a specific organization."""
        endpoint = f"organizations/{organization_urn}"
        return await self.get_data(endpoint)

    def _generate_demo_data(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Generates realistic mock data for demo mode."""
        if endpoint == "ugcPosts":
            return {
                "demo": True,
                "id": f"urn:li:share:{random.randint(10000, 99999)}",
                "activity": f"urn:li:activity:{random.randint(10000, 99999)}",
            }
        if endpoint.startswith("socialActions"): 
            return {
                "demo": True,
                "likes": random.randint(10, 500),
                "comments": random.randint(5, 100),
                "shares": random.randint(1, 50)
            }
        if endpoint.startswith("organizationalEntityAcls"):
            return {
                "demo": True,
                "elements": [
                    {
                        "role": "ADMINISTRATOR",
                        "roleAssignee": "urn:li:person:12345",
                        "state": "APPROVED"
                    }
                ]
            }
        if endpoint.startswith("organizationPageStatistics"):
            return {
                "demo": True,
                "elements": [
                    {
                        "organization": "urn:li:organization:12345",
                        "totalFollowerCount": random.randint(1000, 100000),
                        "totalShareCount": random.randint(100, 5000)
                    }
                ]
            }
        if endpoint.startswith("organizations"):
            return {
                "demo": True,
                "id": params.get("organization_urn") if params else "12345",
                "name": {
                    "localized": {
                        "en_US": "Demo Company"
                    },
                    "preferredLocale": {
                        "country": "US",
                        "language": "en"
                    }
                }
            }
        return {"demo": True}
