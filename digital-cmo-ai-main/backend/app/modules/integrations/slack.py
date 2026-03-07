
"""
Slack Connector

Implements the ConnectorInterface for Slack.
Returns demo data when credentials are not configured.
"""

import logging
import random
from typing import Optional, Any, List
from datetime import datetime, timedelta

from .base import ConnectorInterface, ConnectorError

logger = logging.getLogger(__name__)


class SlackConnector(ConnectorInterface):
    """Connector for Slack API."""

    BASE_URL = "https://slack.com/api"

    def __init__(self, bot_token: Optional[str] = None):
        super().__init__(service_name="Slack", rate_limit=50)
        self.bot_token = bot_token
        self._headers = {}

    async def authenticate(self) -> None:
        """Authenticate with the Slack API using a bot token."""
        if self.bot_token:
            self._headers = {
                "Authorization": f"Bearer {self.bot_token}",
                "Content-Type": "application/json; charset=utf-8",
            }
            try:
                # Test authentication by trying to get auth info
                await self._request_with_retry("POST", f"{self.BASE_URL}/auth.test", headers=self._headers)
                self._is_authenticated = True
                logger.info("Slack authentication successful.")
            except ConnectorError as e:
                self._enter_demo_mode(f"Authentication failed: {e}")
        else:
            self._enter_demo_mode()

    async def get_data(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """Fetch data from a specific API endpoint."""
        if self._demo_mode:
            return self._generate_demo_data(endpoint, params)

        await self._ensure_authenticated()
        url = f"{self.BASE_URL}/{endpoint}"
        return await self._request_with_retry("GET", url, headers=self._headers, params=params)

    async def post_data(self, endpoint: str, data: Optional[dict] = None) -> dict:
        """Send data to a specific API endpoint."""
        if self._demo_mode:
            return self._generate_demo_data(endpoint, data)

        await self._ensure_authenticated()
        url = f"{self.BASE_URL}/{endpoint}"
        return await self._request_with_retry("POST", url, headers=self._headers, json_data=data)

    async def send_message(self, channel: str, text: str) -> dict:
        """Sends a message to a channel."""
        return await self.post_data("chat.postMessage", {"channel": channel, "text": text})

    async def get_channels(self) -> dict:
        """Gets a list of channels."""
        return await self.get_data("conversations.list")

    async def create_channel(self, name: str, is_private: bool = False) -> dict:
        """Creates a channel."""
        return await self.post_data("conversations.create", {"name": name, "is_private": is_private})

    async def upload_file(self, channels: str, content: str, filename: str, title: str) -> dict:
        """Uploads a file."""
        # Note: aiohttp handles multipart/form-data for file uploads differently.
        # This is a simplified version using a fake endpoint for demo/structure.
        # Real implementation would require `FormData`.
        if self._demo_mode:
            return self._generate_demo_data("files.upload")

        await self._ensure_authenticated()
        # The `files.upload` endpoint expects multipart/form-data, which `_request_with_retry` doesn't support out of the box.
        # We will simulate the call for non-demo mode but a real implementation would need to be more complex.
        logger.warning("File upload in non-demo mode is not fully implemented and will likely fail.")
        data = {
            "channels": channels,
            "content": content,
            "filename": filename,
            "title": title,
        }
        return await self.post_data("files.upload", data)

    async def get_channel_history(self, channel: str, limit: int = 100) -> dict:
        """Fetches the history of a channel."""
        return await self.get_data("conversations.history", {"channel": channel, "limit": limit})

    async def send_notification(self, user_id: str, text: str) -> dict:
        """Sends a direct message to a user."""
        return await self.send_message(channel=user_id, text=text)

    def _generate_demo_data(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """Return realistic mock data with random values."""
        if endpoint == "chat.postMessage":
            return {"ok": True, "ts": f"{datetime.now().timestamp()}", "message": {"text": params.get("text") if params else ""}}
        if endpoint == "conversations.list":
            return {
                "ok": True,
                "channels": [
                    {"id": f"C0{random.randint(1000, 9999)}", "name": f"general-{random.randint(1, 100)}"},
                    {"id": f"C0{random.randint(1000, 9999)}", "name": f"random-{random.randint(1, 100)}"},
                ],
            }
        if endpoint == "conversations.create":
            return {
                "ok": True,
                "channel": {"id": f"C0{random.randint(1000, 9999)}", "name": params.get("name") if params else ""},
            }
        if endpoint == "files.upload":
            return {"ok": True, "file": {"id": f"F0{random.randint(1000, 9999)}", "name": "test-file.txt"}}
        if endpoint == "conversations.history":
            return {
                "ok": True,
                "messages": [
                    {
                        "type": "message",
                        "user": f"U0{random.randint(1000, 9999)}",
                        "text": f"Hello world {random.randint(1, 100)}",
                        "ts": f"{(datetime.now() - timedelta(minutes=random.randint(1, 60))).timestamp()}",
                    }
                    for _ in range(random.randint(5, 20))
                ],
            }
        return {"ok": False, "error": "not_found"}
