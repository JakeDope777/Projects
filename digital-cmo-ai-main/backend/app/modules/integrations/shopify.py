'''
Shopify Connector

Implements the ConnectorInterface for Shopify.
Returns demo data when credentials are not configured.
'''

import logging
import random
from typing import Optional, Any
from datetime import datetime, timedelta

from .base import ConnectorInterface

logger = logging.getLogger(__name__)


class ShopifyConnector(ConnectorInterface):
    """Connector for Shopify API."""

    BASE_URL = "https://{shop}.myshopify.com/admin/api/2024-01"

    def __init__(self, shop: Optional[str] = None, api_key: Optional[str] = None, access_token: Optional[str] = None):
        super().__init__(service_name="Shopify", rate_limit=40, rate_window=60)
        self.shop = shop
        self.api_key = api_key
        self.access_token = access_token
        self.headers = {}

        if not all([self.shop, self.api_key, self.access_token]):
            self._enter_demo_mode("Missing shop, api_key, or access_token")
        else:
            self.BASE_URL = self.BASE_URL.format(shop=self.shop)

    async def authenticate(self) -> None:
        """Authenticate with Shopify using API Key and Access Token."""
        if self._demo_mode:
            return

        self.headers = {
            "X-Shopify-Access-Token": self.access_token,
            "Content-Type": "application/json",
        }
        # Test authentication by making a simple request
        try:
            await self.get_data("/shop.json")
            self._is_authenticated = True
            logger.info("Shopify authentication successful.")
        except Exception as e:
            logger.error(f"Shopify authentication failed: {e}")
            self._enter_demo_mode("Authentication failed")

    async def get_data(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """Fetch data from a specific API endpoint."""
        if self._demo_mode:
            return self._generate_demo_data(endpoint, params)

        await self._ensure_authenticated()
        url = f"{self.BASE_URL}{endpoint}"
        return await self._request_with_retry("GET", url, headers=self.headers, params=params)

    async def post_data(self, endpoint: str, data: Optional[dict] = None) -> dict:
        """Send data to a specific API endpoint."""
        if self._demo_mode:
            return {"status": "success", "message": "Demo mode: Data processed."}

        await self._ensure_authenticated()
        url = f"{self.BASE_URL}{endpoint}"
        return await self._request_with_retry("POST", url, headers=self.headers, json_data=data)

    async def get_products(self, limit: int = 50) -> dict:
        """Retrieve a list of products."""
        return await self.get_data("/products.json", params={"limit": limit})

    async def get_orders(self, limit: int = 50, status: str = "any") -> dict:
        """Retrieve a list of orders."""
        return await self.get_data("/orders.json", params={"limit": limit, "status": status})

    async def create_product(self, product_data: dict) -> dict:
        """Create a new product."""
        return await self.post_data("/products.json", data={"product": product_data})

    async def update_inventory(self, inventory_item_id: int, new_quantity: int) -> dict:
        """Update the inventory level for an inventory item."""
        location_id = await self._get_primary_location_id()
        if not location_id:
            return {"error": "Could not determine primary location"}

        inventory_level_data = {
            "inventory_item_id": inventory_item_id,
            "location_id": location_id,
            "available": new_quantity,
        }
        return await self.post_data("/inventory_levels/set.json", data=inventory_level_data)

    async def get_customers(self, limit: int = 50) -> dict:
        """Retrieve a list of customers."""
        return await self.get_data("/customers.json", params={"limit": limit})

    async def get_sales_analytics(self) -> dict:
        """Retrieve sales analytics."""
        # Shopify does not have a direct sales analytics endpoint like this.
        # This is a conceptual method that could be built by aggregating order data.
        if self._demo_mode:
            return self._generate_demo_data("/sales_analytics.json")

        # In a real implementation, we would fetch orders and calculate metrics.
        orders = await self.get_orders(limit=250, status="shipped")
        total_sales = sum(float(order['total_price']) for order in orders.get('orders', []))
        return {"total_sales": total_sales, "order_count": len(orders.get('orders', []))}

    async def _get_primary_location_id(self) -> Optional[int]:
        """Get the primary location ID for inventory updates."""
        if self._demo_mode:
            return 12345
        try:
            locations = await self.get_data("/locations.json")
            if locations and locations.get('locations'):
                return locations['locations'][0]['id']
        except Exception as e:
            logger.error(f"Could not fetch locations: {e}")
        return None

    def _generate_demo_data(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """Return realistic mock data with random values."""
        if endpoint == "/products.json":
            return {
                "products": [
                    {
                        "id": random.randint(1000, 9999),
                        "title": f"Demo Product {i}",
                        "vendor": "Demo Vendor",
                        "product_type": "Demo Type",
                        "variants": [{"price": f"{random.uniform(10, 200):.2f}"}],
                    }
                    for i in range(params.get("limit", 10))
                ]
            }
        if endpoint == "/orders.json":
            return {
                "orders": [
                    {
                        "id": random.randint(10000, 99999),
                        "email": f"customer{i}@example.com",
                        "total_price": f"{random.uniform(50, 500):.2f}",
                        "created_at": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat(),
                    }
                    for i in range(params.get("limit", 10))
                ]
            }
        if endpoint == "/customers.json":
            return {
                "customers": [
                    {
                        "id": random.randint(1000, 9999),
                        "first_name": "John",
                        "last_name": f"Doe{i}",
                        "email": f"johndoe{i}@example.com",
                    }
                    for i in range(params.get("limit", 10))
                ]
            }
        if endpoint == "/sales_analytics.json":
            return {
                "total_sales": random.uniform(5000, 25000),
                "order_count": random.randint(100, 500),
                "top_products": [
                    {"name": "Demo Product A", "sales": random.uniform(1000, 5000)},
                    {"name": "Demo Product B", "sales": random.uniform(500, 2000)},
                ],
            }
        return {}
