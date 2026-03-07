"""
Unit tests for the Integrations & Connectors Module.
"""

import pytest
from app.modules.integrations.base import ConnectorInterface, ConnectorError, RateLimiter
from app.modules.integrations.hubspot import HubSpotConnector
from app.modules.integrations.sendgrid_connector import SendGridConnector
from app.modules.integrations.google_ads import GoogleAdsConnector
from app.modules.integrations.google_analytics import GoogleAnalyticsConnector
from app.modules.integrations.linkedin import LinkedInConnector


class TestRateLimiter:
    """Tests for the rate limiter utility."""

    def test_can_proceed_initially(self):
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        assert limiter.can_proceed() is True

    def test_rate_limit_reached(self):
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        limiter.record_request()
        limiter.record_request()
        assert limiter.can_proceed() is False

    def test_wait_time_zero_when_available(self):
        limiter = RateLimiter(max_requests=10, window_seconds=60)
        assert limiter.wait_time() == 0


class TestConnectorError:
    """Tests for the standardised connector error."""

    def test_error_message_format(self):
        err = ConnectorError("TestService", 429, "Rate limited", "RATE_LIMIT")
        assert "TestService" in str(err)
        assert "429" in str(err)
        assert err.service == "TestService"
        assert err.status_code == 429


class TestHubSpotConnector:
    """Tests for HubSpot connector in demo mode."""

    @pytest.mark.asyncio
    async def test_authenticate_no_key(self):
        connector = HubSpotConnector()
        await connector.authenticate()
        assert connector._is_authenticated is False

    @pytest.mark.asyncio
    async def test_authenticate_with_key(self):
        connector = HubSpotConnector(api_key="test-key")
        await connector.authenticate()
        assert connector._is_authenticated is True

    @pytest.mark.asyncio
    async def test_get_contacts_demo(self):
        connector = HubSpotConnector()
        result = await connector.get_contacts()
        assert result["demo"] is True
        assert "results" in result

    @pytest.mark.asyncio
    async def test_create_contact_demo(self):
        connector = HubSpotConnector()
        result = await connector.create_contact({"firstname": "Test"})
        assert result["demo"] is True


class TestSendGridConnector:
    """Tests for SendGrid connector in demo mode."""

    @pytest.mark.asyncio
    async def test_authenticate_no_key(self):
        connector = SendGridConnector()
        await connector.authenticate()
        assert connector._is_authenticated is False

    @pytest.mark.asyncio
    async def test_send_email_demo(self):
        connector = SendGridConnector()
        result = await connector.send_email(
            "to@example.com", "from@example.com", "Test", "<p>Hello</p>"
        )
        assert result["demo"] is True


class TestGoogleAdsConnector:
    """Tests for Google Ads connector in demo mode."""

    @pytest.mark.asyncio
    async def test_authenticate_no_credentials(self):
        connector = GoogleAdsConnector()
        await connector.authenticate()
        assert connector._is_authenticated is False

    @pytest.mark.asyncio
    async def test_get_campaign_metrics_demo(self):
        connector = GoogleAdsConnector()
        result = await connector.get_campaign_metrics()
        assert result["demo"] is True
        assert "campaigns" in result
        assert len(result["campaigns"]) > 0


class TestGoogleAnalyticsConnector:
    """Tests for Google Analytics connector in demo mode."""

    @pytest.mark.asyncio
    async def test_get_website_metrics_demo(self):
        connector = GoogleAnalyticsConnector()
        result = await connector.get_website_metrics()
        assert result["demo"] is True
        assert "metrics" in result
        assert "top_pages" in result


class TestLinkedInConnector:
    """Tests for LinkedIn connector in demo mode."""

    @pytest.mark.asyncio
    async def test_create_post_demo(self):
        connector = LinkedInConnector()
        result = await connector.create_post("Test post content")
        assert result["demo"] is True

    @pytest.mark.asyncio
    async def test_get_post_analytics_demo(self):
        connector = LinkedInConnector()
        result = await connector.get_post_analytics("post-123")
        assert result["demo"] is True
