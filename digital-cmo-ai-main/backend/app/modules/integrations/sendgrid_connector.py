'''
SendGrid Connector

Implements the ConnectorInterface for SendGrid.
Returns demo data when credentials are not configured.
'''

import logging
import random
from typing import Optional, Any, List
from datetime import datetime, timedelta

from .base import ConnectorInterface

logger = logging.getLogger(__name__)


class SendGridConnector(ConnectorInterface):
    """Connector for SendGrid API."""

    BASE_URL = "https://api.sendgrid.com/v3"

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(service_name="SendGrid", rate_limit=100)
        self.api_key = api_key
        if not self.api_key:
            self._enter_demo_mode()

    async def authenticate(self) -> None:
        """Authenticate with SendGrid using the API key."""
        if self.api_key:
            self._is_authenticated = True
            logger.info("[SendGrid] Authenticated using API key.")
        else:
            self._enter_demo_mode()

    async def get_data(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """Fetch data from a specific API endpoint."""
        if self._demo_mode:
            return self._generate_demo_data(endpoint, params)

        await self._ensure_authenticated()
        headers = {"Authorization": f"Bearer {self.api_key}"}
        url = f"{self.BASE_URL}/{endpoint}"
        return await self._request_with_retry("GET", url, headers=headers, params=params)

    async def post_data(self, endpoint: str, data: Optional[dict] = None) -> dict:
        """Send data to a specific API endpoint."""
        if self._demo_mode:
            return {"demo": True, "status": "success", "message": "Demo request sent"}

        await self._ensure_authenticated()
        headers = {"Authorization": f"Bearer {self.api_key}"}
        url = f"{self.BASE_URL}/{endpoint}"
        return await self._request_with_retry("POST", url, headers=headers, json_data=data)

    async def send_email(self, to_email: str, from_email: str, subject: str, content: str) -> dict:
        """Sends an email."""
        data = {
            "personalizations": [{"to": [{"email": to_email}]}],
            "from": {"email": from_email},
            "subject": subject,
            "content": [{"type": "text/plain", "value": content}],
        }
        return await self.post_data("mail/send", data)

    async def send_template_email(self, to_email: str, from_email: str, template_id: str, template_data: dict) -> dict:
        """Sends an email using a template."""
        data = {
            "personalizations": [
                {
                    "to": [{"email": to_email}],
                    "dynamic_template_data": template_data,
                }
            ],
            "from": {"email": from_email},
            "template_id": template_id,
        }
        return await self.post_data("mail/send", data)

    async def get_email_stats(self, start_date: str, end_date: str) -> dict:
        """Gets email statistics."""
        params = {"start_date": start_date, "end_date": end_date}
        return await self.get_data("stats", params)

    async def get_bounces(self) -> dict:
        """Gets a list of bounced emails."""
        return await self.get_data("suppression/bounces")

    async def get_contacts(self) -> dict:
        """Gets a list of all contacts."""
        return await self.get_data("marketing/contacts")

    async def add_contacts_to_list(self, list_id: str, contacts: List[dict]) -> dict:
        """Adds contacts to a specific list."""
        data = {"list_ids": [list_id], "contacts": contacts}
        return await self.post_data("marketing/contacts", data)

    def _generate_demo_data(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """Generates realistic mock data for demo mode."""
        if endpoint == "stats":
            return {
                "demo": True,
                "stats": [
                    {
                        "metrics": {
                            "blocks": random.randint(0, 10),
                            "bounce_drops": random.randint(0, 5),
                            "bounces": random.randint(0, 10),
                            "clicks": random.randint(100, 500),
                            "deferred": random.randint(0, 20),
                            "delivered": random.randint(1000, 2000),
                            "invalid_emails": random.randint(0, 5),
                            "opens": random.randint(500, 1500),
                            "processed": random.randint(1000, 2000),
                            "requests": random.randint(1000, 2000),
                            "spam_report_drops": random.randint(0, 2),
                            "spam_reports": random.randint(0, 5),
                            "unique_clicks": random.randint(50, 200),
                            "unique_opens": random.randint(200, 800),
                            "unsubscribe_drops": random.randint(0, 3),
                            "unsubscribes": random.randint(0, 10),
                        }
                    }
                ]
            }
        if endpoint == "suppression/bounces":
            return {
                "demo": True,
                "bounces": [
                    {
                        "created": int((datetime.now() - timedelta(days=random.randint(1, 30))).timestamp()),
                        "email": f"bounce{i}@example.com",
                        "reason": "550 5.1.1 The email account that you tried to reach does not exist.",
                        "status": "5.1.1",
                    }
                    for i in range(random.randint(1, 5))
                ]
            }
        if endpoint == "marketing/contacts":
            return {
                "demo": True,
                "result": [
                    {
                        "id": f"contact-id-{i}",
                        "email": f"contact{i}@example.com",
                        "first_name": "John",
                        "last_name": f"Doe{i}",
                    }
                    for i in range(random.randint(5, 20))
                ]
            }
        return {"demo": True}
