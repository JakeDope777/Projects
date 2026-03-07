'''
Stripe Connector

Implements the ConnectorInterface for Stripe.
Returns demo data when credentials are not configured.
'''

import logging
import random
from typing import Optional, Any
from datetime import datetime, timedelta

from .base import ConnectorInterface, ConnectorError

logger = logging.getLogger(__name__)


class StripeConnector(ConnectorInterface):
    """Connector for Stripe API."""

    BASE_URL = "https://api.stripe.com/v1"

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(service_name="Stripe", rate_limit=100)
        self.api_key = api_key

    async def authenticate(self) -> None:
        """Authenticate with the Stripe API using an API key."""
        if not self.api_key:
            self._enter_demo_mode()
            return

        self._is_authenticated = True
        logger.info("[Stripe] Authenticated successfully.")

    async def get_data(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """Fetch data from a specific Stripe API endpoint."""
        if self._demo_mode:
            return self._generate_demo_data(endpoint, params)

        await self._ensure_authenticated()
        url = f"{self.BASE_URL}/{endpoint}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        return await self._request_with_retry("GET", url, headers=headers, params=params)

    async def post_data(self, endpoint: str, data: Optional[dict] = None) -> dict:
        """Send data to a specific Stripe API endpoint."""
        if self._demo_mode:
            return self._generate_demo_data(endpoint, data)

        await self._ensure_authenticated()
        url = f"{self.BASE_URL}/{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        return await self._request_with_retry("POST", url, headers=headers, params=data)

    async def get_payments(self, limit: int = 10) -> dict:
        """Retrieve a list of payments."""
        return await self.get_data("charges", params={"limit": limit})

    async def get_customers(self, limit: int = 10) -> dict:
        """Retrieve a list of customers."""
        return await self.get_data("customers", params={"limit": limit})

    async def create_payment_intent(self, amount: int, currency: str) -> dict:
        """Create a payment intent."""
        return await self.post_data(
            "payment_intents",
            data={"amount": amount, "currency": currency},
        )

    async def get_subscriptions(self, limit: int = 10) -> dict:
        """Retrieve a list of subscriptions."""
        return await self.get_data("subscriptions", params={"limit": limit})

    async def get_revenue_metrics(self, start_date: str, end_date: str) -> dict:
        """Get revenue metrics for a given period."""
        # This is a simplified example. Real implementation might involve more complex logic.
        if self._demo_mode:
            return self._generate_demo_data("balance_transactions")

        return await self.get_data(
            "balance_transactions",
            params={
                "created[gte]": int(datetime.strptime(start_date, "%Y-%m-%d").timestamp()),
                "created[lte]": int(datetime.strptime(end_date, "%Y-%m-%d").timestamp()),
                "type": "charge",
            },
        )

    async def create_customer(self, email: str, name: str) -> dict:
        """Create a new customer."""
        return await self.post_data("customers", data={"email": email, "name": name})

    def _generate_demo_data(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """Generate realistic mock data for Stripe endpoints."""
        if endpoint == "charges":
            return {
                "data": [
                    {
                        "id": f"ch_{random.randint(1000, 9999)}",
                        "amount": random.randint(1000, 50000),
                        "currency": "usd",
                        "status": random.choice(["succeeded", "failed"]),
                        "created": int((datetime.now() - timedelta(days=random.randint(1, 30))).timestamp()),
                    }
                    for _ in range(params.get("limit", 10))
                ]
            }
        if endpoint == "customers":
            return {
                "data": [
                    {
                        "id": f"cus_{random.randint(1000, 9999)}",
                        "email": f"customer{random.randint(1, 100)}@example.com",
                        "name": f"Customer {random.randint(1, 100)}",
                        "created": int((datetime.now() - timedelta(days=random.randint(1, 90))).timestamp()),
                    }
                    for _ in range(params.get("limit", 10))
                ]
            }
        if endpoint == "payment_intents":
            return {
                "id": f"pi_{random.randint(1000, 9999)}",
                "amount": params.get("amount", 2000),
                "currency": params.get("currency", "usd"),
                "status": "requires_payment_method",
            }
        if endpoint == "subscriptions":
            return {
                "data": [
                    {
                        "id": f"sub_{random.randint(1000, 9999)}",
                        "customer": f"cus_{random.randint(1000, 9999)}",
                        "status": random.choice(["active", "canceled"]),
                        "current_period_end": int((datetime.now() + timedelta(days=random.randint(15, 45))).timestamp()),
                    }
                    for _ in range(params.get("limit", 10))
                ]
            }
        if endpoint == "balance_transactions":
            return {
                "data": [
                    {
                        "id": f"txn_{random.randint(1000, 9999)}",
                        "amount": random.randint(1000, 20000),
                        "net": random.randint(900, 18000),
                        "currency": "usd",
                        "created": int((datetime.now() - timedelta(days=random.randint(1, 30))).timestamp()),
                    }
                    for _ in range(random.randint(5, 20))
                ]
            }
        return {}
