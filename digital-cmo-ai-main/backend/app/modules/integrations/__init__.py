"""
Integrations & Connectors Module
=================================

Provides unified API connectors for 20 major marketing, advertising,
CRM, analytics, e-commerce, SEO, communication, and payment platforms.

Each connector inherits from ConnectorInterface and supports:
- Real API authentication (OAuth2, API key, Bearer token, Basic Auth)
- Core read/write operations
- Rate limiting with exponential-backoff retry logic
- Demo/mock fallback mode when credentials are not configured
- Standardised error handling via ConnectorError

Usage:
    from backend.app.modules.integrations import ConnectorRegistry
    registry = ConnectorRegistry()
    connector = registry.get("google_ads")
"""

# Base classes
from .base import ConnectorInterface, ConnectorError, RateLimiter

# --- Advertising Platforms ---
from .google_ads import GoogleAdsConnector
from .meta_ads import MetaAdsConnector
from .tiktok_ads import TikTokAdsConnector

# --- Social Media Platforms ---
from .linkedin import LinkedInConnector
from .twitter import TwitterConnector
from .facebook_pages import FacebookPagesConnector

# --- Email Marketing ---
from .sendgrid_connector import SendGridConnector
from .mailchimp import MailchimpConnector

# --- CRM Systems ---
from .hubspot import HubSpotConnector
from .salesforce import SalesforceConnector
from .zoho_crm import ZohoCRMConnector

# --- Analytics & Data ---
from .google_analytics import GoogleAnalyticsConnector
from .mixpanel import MixpanelConnector

# --- E-commerce & Payments ---
from .shopify import ShopifyConnector
from .stripe import StripeConnector

# --- Marketing Automation ---
from .activecampaign import ActiveCampaignConnector
from .klaviyo import KlaviyoConnector

# --- SEO Tools ---
from .semrush import SEMrushConnector

# --- Communication / Messaging ---
from .slack import SlackConnector
from .twilio import TwilioConnector


# ---------------------------------------------------------------------------
# Connector Registry
# ---------------------------------------------------------------------------

class ConnectorRegistry:
    """
    Central registry that manages all available connectors.

    Provides factory methods to instantiate connectors by name,
    list available integrations, and check their status.
    """

    CONNECTOR_MAP: dict[str, type] = {
        # Advertising
        "google_ads": GoogleAdsConnector,
        "meta_ads": MetaAdsConnector,
        "tiktok_ads": TikTokAdsConnector,
        # Social Media
        "linkedin": LinkedInConnector,
        "twitter": TwitterConnector,
        "facebook_pages": FacebookPagesConnector,
        # Email Marketing
        "sendgrid": SendGridConnector,
        "mailchimp": MailchimpConnector,
        # CRM
        "hubspot": HubSpotConnector,
        "salesforce": SalesforceConnector,
        "zoho_crm": ZohoCRMConnector,
        # Analytics
        "google_analytics": GoogleAnalyticsConnector,
        "mixpanel": MixpanelConnector,
        # E-commerce & Payments
        "shopify": ShopifyConnector,
        "stripe": StripeConnector,
        # Marketing Automation
        "activecampaign": ActiveCampaignConnector,
        "klaviyo": KlaviyoConnector,
        # SEO
        "semrush": SEMrushConnector,
        # Communication
        "slack": SlackConnector,
        "twilio": TwilioConnector,
    }

    CATEGORIES: dict[str, list[str]] = {
        "advertising": ["google_ads", "meta_ads", "tiktok_ads"],
        "social_media": ["linkedin", "twitter", "facebook_pages"],
        "email_marketing": ["sendgrid", "mailchimp"],
        "crm": ["hubspot", "salesforce", "zoho_crm"],
        "analytics": ["google_analytics", "mixpanel"],
        "ecommerce_payments": ["shopify", "stripe"],
        "marketing_automation": ["activecampaign", "klaviyo"],
        "seo": ["semrush"],
        "communication": ["slack", "twilio"],
    }

    def __init__(self):
        self._instances: dict[str, ConnectorInterface] = {}

    def get(self, name: str, **kwargs) -> ConnectorInterface:
        """
        Get or create a connector instance by name.

        Args:
            name: Connector key (e.g. 'google_ads', 'hubspot').
            **kwargs: Credentials and configuration passed to the constructor.

        Returns:
            An instance of the requested connector.

        Raises:
            ValueError: If the connector name is not registered.
        """
        if name not in self.CONNECTOR_MAP:
            raise ValueError(
                f"Unknown connector '{name}'. "
                f"Available: {list(self.CONNECTOR_MAP.keys())}"
            )

        cache_key = f"{name}:{hash(frozenset(kwargs.items()))}"
        if cache_key not in self._instances:
            self._instances[cache_key] = self.CONNECTOR_MAP[name](**kwargs)
        return self._instances[cache_key]

    def list_connectors(self) -> list[dict]:
        """Return metadata for every registered connector."""
        result = []
        for key, cls in self.CONNECTOR_MAP.items():
            category = next(
                (cat for cat, members in self.CATEGORIES.items() if key in members),
                "other",
            )
            result.append(
                {
                    "key": key,
                    "class": cls.__name__,
                    "category": category,
                    "base_url": getattr(cls, "BASE_URL", None),
                }
            )
        return result

    def list_categories(self) -> dict[str, list[str]]:
        """Return the category-to-connector mapping."""
        return dict(self.CATEGORIES)

    def get_all_status(self) -> list[dict]:
        """Return the status of every instantiated connector."""
        return [inst.get_status() for inst in self._instances.values()]


__all__ = [
    # Base
    "ConnectorInterface",
    "ConnectorError",
    "RateLimiter",
    "ConnectorRegistry",
    # Advertising
    "GoogleAdsConnector",
    "MetaAdsConnector",
    "TikTokAdsConnector",
    # Social Media
    "LinkedInConnector",
    "TwitterConnector",
    "FacebookPagesConnector",
    # Email Marketing
    "SendGridConnector",
    "MailchimpConnector",
    # CRM
    "HubSpotConnector",
    "SalesforceConnector",
    "ZohoCRMConnector",
    # Analytics
    "GoogleAnalyticsConnector",
    "MixpanelConnector",
    # E-commerce & Payments
    "ShopifyConnector",
    "StripeConnector",
    # Marketing Automation
    "ActiveCampaignConnector",
    "KlaviyoConnector",
    # SEO
    "SEMrushConnector",
    # Communication
    "SlackConnector",
    "TwilioConnector",
]
