
"""
Twitter/X Connector

Implements the ConnectorInterface for Twitter/X.
Returns demo data when credentials are not configured.
"""

import logging
import random
from typing import Optional, Any
from datetime import datetime, timedelta

from .base import ConnectorInterface, ConnectorError

logger = logging.getLogger(__name__)


class TwitterConnector(ConnectorInterface):
    """Connector for Twitter/X API."""

    BASE_URL = "https://api.twitter.com/2"

    def __init__(self, bearer_token: Optional[str] = None):
        super().__init__(service_name="Twitter", rate_limit=40)
        self.bearer_token = bearer_token
        self._is_authenticated = False

    async def authenticate(self) -> None:
        """Authenticate with the Twitter API using a Bearer Token."""
        if self.bearer_token:
            self._is_authenticated = True
            logger.info("Twitter connector authenticated with Bearer Token.")
        else:
            self._enter_demo_mode()

    async def get_data(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """Fetch data from a specific API endpoint."""
        if self._demo_mode:
            return self._generate_demo_data(endpoint, params)

        await self._ensure_authenticated()
        headers = {"Authorization": f"Bearer {self.bearer_token}"}
        url = f"{self.BASE_URL}/{endpoint}"
        return await self._request_with_retry("GET", url, headers=headers, params=params)

    async def post_data(self, endpoint: str, data: Optional[dict] = None) -> dict:
        """Send data to a specific API endpoint."""
        if self._demo_mode:
            return self._generate_demo_data(endpoint)

        await self._ensure_authenticated()
        headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json",
        }
        url = f"{self.BASE_URL}/{endpoint}"
        return await self._request_with_retry("POST", url, headers=headers, json_data=data)

    async def delete_data(self, endpoint: str) -> dict:
        """Delete data from a specific API endpoint."""
        if self._demo_mode:
            return {"data": {"deleted": True}}

        await self._ensure_authenticated()
        headers = {"Authorization": f"Bearer {self.bearer_token}"}
        url = f"{self.BASE_URL}/{endpoint}"
        return await self._request_with_retry("DELETE", url, headers=headers)

    async def create_tweet(self, text: str) -> dict:
        """Creates a new tweet."""
        return await self.post_data("tweets", {"text": text})

    async def get_tweet_metrics(self, tweet_id: str) -> dict:
        """Retrieves metrics for a specific tweet."""
        return await self.get_data(f"tweets/{tweet_id}", {"tweet.fields": "public_metrics"})

    async def get_user_timeline(self, user_id: str, max_results: int = 10) -> dict:
        """Retrieves the timeline of a specific user."""
        return await self.get_data(f"users/{user_id}/tweets", {"max_results": max_results})

    async def search_tweets(self, query: str, max_results: int = 10) -> dict:
        """Searches for recent tweets matching a query."""
        return await self.get_data("tweets/search/recent", {"query": query, "max_results": max_results})

    async def get_followers_count(self, user_id: str) -> dict:
        """Gets the follower count for a user."""
        return await self.get_data(f"users/{user_id}", {"user.fields": "public_metrics"})

    async def delete_tweet(self, tweet_id: str) -> dict:
        """Deletes a specific tweet."""
        return await self.delete_data(f"tweets/{tweet_id}")

    def _generate_demo_data(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """Return realistic mock data with random values."""
        if "tweets" in endpoint and "search" not in endpoint and "users" not in endpoint:
            if "public_metrics" in (params or {}).get("tweet.fields", ""):
                return {
                    "data": {
                        "id": str(random.randint(10**18, 10**19 - 1)),
                        "text": "This is a tweet.",
                        "public_metrics": {
                            "retweet_count": random.randint(0, 100),
                            "reply_count": random.randint(0, 50),
                            "like_count": random.randint(0, 500),
                            "quote_count": random.randint(0, 20),
                        },
                    }
                }
            return {
                "data": {
                    "id": str(random.randint(10**18, 10**19 - 1)),
                    "text": "This is a tweet about something interesting.",
                }
            }
        if "users" in endpoint and "tweets" in endpoint:
            return {
                "data": [
                    {
                        "id": str(random.randint(10**18, 10**19 - 1)),
                        "text": f"This is a demo tweet from user timeline {i}",
                    }
                    for i in range(params.get("max_results", 5))
                ],
                "meta": {"result_count": params.get("max_results", 5)},
            }
        if "users" in endpoint:
            return {
                "data": {
                    "id": str(random.randint(1, 1000)),
                    "name": "Demo User",
                    "username": "demouser",
                    "public_metrics": {"followers_count": random.randint(100, 10000)},
                }
            }
        if "search" in endpoint:
            return {
                "data": [
                    {
                        "id": str(random.randint(10**18, 10**19 - 1)),
                        "text": f"This is a demo search result tweet {i}",
                    }
                    for i in range(params.get("max_results", 5))
                ],
                "meta": {"result_count": params.get("max_results", 5)},
            }
        return {}
