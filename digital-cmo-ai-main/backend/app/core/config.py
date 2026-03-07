"""
Application configuration using Pydantic settings.
Reads from environment variables and .env files.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Global application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Digital CMO AI"
    APP_VERSION: str = "0.2.0"
    DEBUG: bool = True

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: str = "sqlite:///./data/digital_cmo.db"

    # JWT Authentication
    SECRET_KEY: str = "change-me-in-production-use-a-strong-random-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # LLM Configuration
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4.1-mini"
    OPENAI_BASE_URL: Optional[str] = None

    # Vector Database (FAISS)
    VECTOR_DB_PATH: str = "./data/vector_store"
    EMBEDDING_MODEL: str = "text-embedding-ada-002"
    EMBEDDING_DIMENSION: int = 1536

    # Memory
    MEMORY_BASE_PATH: str = "./memory"

    # ── External Integrations ──────────────────────────────────────────

    # Advertising Platforms
    GOOGLE_ADS_CLIENT_ID: Optional[str] = None
    GOOGLE_ADS_CLIENT_SECRET: Optional[str] = None
    GOOGLE_ADS_DEVELOPER_TOKEN: Optional[str] = None
    META_ADS_ACCESS_TOKEN: Optional[str] = None
    META_ADS_APP_ID: Optional[str] = None
    META_ADS_APP_SECRET: Optional[str] = None
    TIKTOK_ADS_ACCESS_TOKEN: Optional[str] = None
    TIKTOK_ADS_ADVERTISER_ID: Optional[str] = None

    # Social Media Platforms
    LINKEDIN_CLIENT_ID: Optional[str] = None
    LINKEDIN_CLIENT_SECRET: Optional[str] = None
    TWITTER_BEARER_TOKEN: Optional[str] = None
    TWITTER_API_KEY: Optional[str] = None
    TWITTER_API_SECRET: Optional[str] = None
    FACEBOOK_PAGE_ACCESS_TOKEN: Optional[str] = None
    FACEBOOK_PAGE_ID: Optional[str] = None

    # Email Marketing
    SENDGRID_API_KEY: Optional[str] = None
    MAILCHIMP_API_KEY: Optional[str] = None

    # CRM Systems
    HUBSPOT_API_KEY: Optional[str] = None
    HUBSPOT_ACCESS_TOKEN: Optional[str] = None
    SALESFORCE_CLIENT_ID: Optional[str] = None
    SALESFORCE_CLIENT_SECRET: Optional[str] = None
    SALESFORCE_USERNAME: Optional[str] = None
    SALESFORCE_PASSWORD: Optional[str] = None
    SALESFORCE_INSTANCE_URL: Optional[str] = None
    ZOHO_CLIENT_ID: Optional[str] = None
    ZOHO_CLIENT_SECRET: Optional[str] = None
    ZOHO_REFRESH_TOKEN: Optional[str] = None

    # Analytics & Data
    GOOGLE_ANALYTICS_PROPERTY_ID: Optional[str] = None
    GOOGLE_ANALYTICS_CREDENTIALS_JSON: Optional[str] = None
    MIXPANEL_API_SECRET: Optional[str] = None
    MIXPANEL_PROJECT_ID: Optional[str] = None

    # E-commerce & Payments
    SHOPIFY_SHOP_NAME: Optional[str] = None
    SHOPIFY_ACCESS_TOKEN: Optional[str] = None
    STRIPE_SECRET_KEY: Optional[str] = None

    # Marketing Automation
    ACTIVECAMPAIGN_API_KEY: Optional[str] = None
    ACTIVECAMPAIGN_ACCOUNT_URL: Optional[str] = None
    KLAVIYO_API_KEY: Optional[str] = None

    # SEO Tools
    SEMRUSH_API_KEY: Optional[str] = None

    # Communication / Messaging
    SLACK_BOT_TOKEN: Optional[str] = None
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None

    # Token Accounting
    FREE_TIER_MONTHLY_TOKENS: int = 10000
    PRO_TIER_MONTHLY_TOKENS: int = 100000
    ENTERPRISE_TIER_MONTHLY_TOKENS: int = 1000000

    # CORS
    CORS_ORIGINS: list[str] = ["*"]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


settings = Settings()
