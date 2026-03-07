'''
Twilio Connector

Implements the ConnectorInterface for Twilio.
Returns demo data when credentials are not configured.
'''

import logging
import random
import base64
from typing import Optional, Any
from datetime import datetime, timedelta

from .base import ConnectorInterface, ConnectorError

logger = logging.getLogger(__name__)


class TwilioConnector(ConnectorInterface):
    """Connector for Twilio API."""

    BASE_URL = "https://api.twilio.com/2010-04-01"

    def __init__(self, account_sid: Optional[str] = None, auth_token: Optional[str] = None):
        super().__init__(service_name="Twilio", rate_limit=60)
        self.account_sid = account_sid
        self.auth_token = auth_token
        self._auth_header = None

    async def authenticate(self) -> None:
        """Authenticate with Twilio using Account SID and Auth Token."""
        if self.account_sid and self.auth_token:
            try:
                auth_str = f"{self.account_sid}:{self.auth_token}"
                auth_bytes = auth_str.encode('ascii')
                auth_b64 = base64.b64encode(auth_bytes)
                self._auth_header = {'Authorization': f'Basic {auth_b64.decode("ascii")}'}
                # Test authentication by fetching account details
                await self.get_account_usage()
                self._is_authenticated = True
                logger.info("Twilio authentication successful.")
            except ConnectorError as e:
                self._enter_demo_mode(f"Authentication failed: {e}")
        else:
            self._enter_demo_mode()

    async def get_data(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """Fetch data from a specific API endpoint."""
        if self._demo_mode:
            return self._generate_demo_data(endpoint, params)

        await self._ensure_authenticated()
        url = f"{self.BASE_URL}{endpoint}"
        return await self._request_with_retry("GET", url, headers=self._auth_header, params=params)

    async def post_data(self, endpoint: str, data: Optional[dict] = None) -> dict:
        """Send data to a specific API endpoint."""
        if self._demo_mode:
            return self._generate_demo_data(endpoint, data)

        await self._ensure_authenticated()
        url = f"{self.BASE_URL}{endpoint}"
        return await self._request_with_retry("POST", url, headers=self._auth_header, json_data=data)

    async def send_sms(self, to: str, from_: str, body: str) -> dict:
        """Send an SMS message."""
        endpoint = f"/Accounts/{self.account_sid}/Messages.json"
        data = {'To': to, 'From': from_, 'Body': body}
        return await self.post_data(endpoint, data)

    async def send_whatsapp(self, to: str, from_: str, body: str) -> dict:
        """Send a WhatsApp message."""
        endpoint = f"/Accounts/{self.account_sid}/Messages.json"
        data = {'To': f"whatsapp:{to}", 'From': f"whatsapp:{from_}", 'Body': body}
        return await self.post_data(endpoint, data)

    async def get_message_status(self, message_sid: str) -> dict:
        """Get the status of a specific message."""
        endpoint = f"/Accounts/{self.account_sid}/Messages/{message_sid}.json"
        return await self.get_data(endpoint)

    async def get_messages(self, limit: int = 20) -> dict:
        """Get a list of messages."""
        endpoint = f"/Accounts/{self.account_sid}/Messages.json"
        params = {'PageSize': limit}
        return await self.get_data(endpoint, params)

    async def make_call(self, to: str, from_: str, url: str) -> dict:
        """Make a phone call."""
        endpoint = f"/Accounts/{self.account_sid}/Calls.json"
        data = {'To': to, 'From': from_, 'Url': url}
        return await self.post_data(endpoint, data)

    async def get_account_usage(self) -> dict:
        """Get account usage records."""
        endpoint = f"/Accounts/{self.account_sid}/Usage/Records.json"
        return await self.get_data(endpoint)

    def _generate_demo_data(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """Generate mock data for demo mode."""
        if "Messages.json" in endpoint and params and "PageSize" in params:
            return {
                "messages": [
                    {
                        "sid": f"SM{random.randint(1000, 9999)}",
                        "status": random.choice(["queued", "sent", "delivered", "failed"]),
                        "to": f"+1555{random.randint(1000000, 9999999)}",
                        "from": f"+1555{random.randint(1000000, 9999999)}",
                        "body": "This is a demo message.",
                        "date_sent": (datetime.now() - timedelta(minutes=random.randint(1, 60))).isoformat(),
                    }
                    for _ in range(params.get("PageSize", 20))
                ]
            }
        if "Messages.json" in endpoint:
            return {
                "sid": f"SM{random.randint(1000, 9999)}",
                "status": "queued",
            }
        if "Calls.json" in endpoint:
            return {
                "sid": f"CA{random.randint(1000, 9999)}",
                "status": "queued",
            }
        if "Usage/Records.json" in endpoint:
            return {
                "usage_records": [
                    {
                        "category": "sms-outbound",
                        "usage": str(random.randint(100, 1000)),
                        "usage_unit": "messages",
                        "price": str(random.uniform(0.01, 0.1)),
                        "price_unit": "usd",
                    }
                ]
            }
        return {}
