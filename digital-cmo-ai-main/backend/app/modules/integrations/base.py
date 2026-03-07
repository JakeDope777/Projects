"""
Base Connector Interface

All integration connectors inherit from this abstract class, ensuring
a consistent API for authentication, data retrieval, data posting,
error handling, rate limiting, retry logic, and demo/mock fallback.
"""

import time
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Optional, Any

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple in-memory rate limiter with exponential backoff."""

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: list[float] = []

    def can_proceed(self) -> bool:
        """Check if a request can proceed within the rate limit."""
        now = time.time()
        self._requests = [t for t in self._requests if now - t < self.window_seconds]
        return len(self._requests) < self.max_requests

    def record_request(self):
        """Record that a request was made."""
        self._requests.append(time.time())

    def wait_time(self) -> float:
        """Calculate how long to wait before the next request."""
        if self.can_proceed():
            return 0
        oldest = min(self._requests)
        return max(0, self.window_seconds - (time.time() - oldest))


class ConnectorInterface(ABC):
    """
    Abstract base class for all external service connectors.

    Provides a unified interface for authentication, data operations,
    error handling, rate limiting, retry logic, and demo/mock fallback.
    """

    def __init__(
        self,
        service_name: str,
        api_key: Optional[str] = None,
        rate_limit: int = 100,
        rate_window: int = 60,
        max_retries: int = 3,
        retry_backoff: float = 1.0,
    ):
        self.service_name = service_name
        self.api_key = api_key
        self.rate_limiter = RateLimiter(
            max_requests=rate_limit, window_seconds=rate_window
        )
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff
        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = None
        self._token_expires_at: Optional[float] = None
        self._is_authenticated = False
        self._demo_mode = False

    @property
    def demo_mode(self) -> bool:
        """Whether the connector is running in demo/mock mode."""
        return self._demo_mode

    @abstractmethod
    async def authenticate(self) -> None:
        """Handle authentication and set internal tokens."""
        pass

    @abstractmethod
    async def get_data(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """Fetch data from a specific API endpoint."""
        pass

    @abstractmethod
    async def post_data(self, endpoint: str, data: Optional[dict] = None) -> dict:
        """Send data to a specific API endpoint."""
        pass

    def handle_error(self, response: dict) -> "ConnectorError":
        """Convert API error responses into standardised exceptions."""
        status = response.get("status_code", 500)
        message = response.get("message", "Unknown error")
        error_code = response.get("error_code", "UNKNOWN")

        error = ConnectorError(
            service=self.service_name,
            status_code=status,
            message=message,
            error_code=error_code,
        )
        logger.error(f"[{self.service_name}] Error {status}: {message}")
        return error

    async def refresh_access_token(self) -> None:
        """Refresh the access token if expired. Override in subclasses."""
        logger.info(f"[{self.service_name}] Token refresh not implemented.")

    def is_token_expired(self) -> bool:
        """Check if the current access token has expired."""
        if self._token_expires_at is None:
            return True
        return time.time() >= self._token_expires_at

    async def _ensure_authenticated(self):
        """Ensure the connector is authenticated before making requests."""
        if not self._is_authenticated or self.is_token_expired():
            await self.authenticate()

    async def _check_rate_limit(self):
        """Check rate limit and wait if necessary."""
        if not self.rate_limiter.can_proceed():
            wait = self.rate_limiter.wait_time()
            logger.warning(
                f"[{self.service_name}] Rate limit reached. Waiting {wait:.1f}s."
            )
            await asyncio.sleep(wait)
        self.rate_limiter.record_request()

    async def _request_with_retry(
        self,
        method: str,
        url: str,
        headers: Optional[dict] = None,
        params: Optional[dict] = None,
        json_data: Optional[dict] = None,
    ) -> dict:
        """
        Execute an HTTP request with exponential-backoff retry logic.

        Returns the parsed JSON response or raises ConnectorError.
        """
        import aiohttp

        last_error: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                await self._check_rate_limit()
                async with aiohttp.ClientSession() as session:
                    async with session.request(
                        method,
                        url,
                        headers=headers,
                        params=params,
                        json=json_data,
                        timeout=aiohttp.ClientTimeout(total=30),
                    ) as resp:
                        body = await resp.json(content_type=None)
                        if resp.status >= 400:
                            # Retry on 429 (rate limit) and 5xx (server errors)
                            if resp.status == 429 or resp.status >= 500:
                                raise ConnectorError(
                                    service=self.service_name,
                                    status_code=resp.status,
                                    message=str(body),
                                    error_code="RETRYABLE",
                                )
                            # Non-retryable client error
                            raise ConnectorError(
                                service=self.service_name,
                                status_code=resp.status,
                                message=str(body),
                                error_code="CLIENT_ERROR",
                            )
                        return body
            except ConnectorError as e:
                last_error = e
                if e.error_code != "RETRYABLE":
                    raise
                wait = self.retry_backoff * (2 ** (attempt - 1))
                logger.warning(
                    f"[{self.service_name}] Attempt {attempt}/{self.max_retries} "
                    f"failed ({e.status_code}). Retrying in {wait:.1f}s..."
                )
                await asyncio.sleep(wait)
            except Exception as e:
                last_error = e
                wait = self.retry_backoff * (2 ** (attempt - 1))
                logger.warning(
                    f"[{self.service_name}] Attempt {attempt}/{self.max_retries} "
                    f"error: {e}. Retrying in {wait:.1f}s..."
                )
                await asyncio.sleep(wait)

        raise ConnectorError(
            service=self.service_name,
            status_code=0,
            message=f"All {self.max_retries} retries exhausted. Last error: {last_error}",
            error_code="MAX_RETRIES_EXCEEDED",
        )

    def _enter_demo_mode(self, reason: str = "No credentials configured"):
        """Switch the connector to demo/mock mode."""
        self._demo_mode = True
        self._is_authenticated = False
        logger.warning(
            f"[{self.service_name}] {reason}. Running in DEMO mode."
        )

    def get_status(self) -> dict:
        """Return the current status of this connector."""
        return {
            "service": self.service_name,
            "authenticated": self._is_authenticated,
            "demo_mode": self._demo_mode,
            "token_expired": self.is_token_expired(),
        }


class ConnectorError(Exception):
    """Standardised error for connector failures."""

    def __init__(
        self,
        service: str,
        status_code: int,
        message: str,
        error_code: str = "UNKNOWN",
    ):
        self.service = service
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(f"[{service}] {status_code} - {error_code}: {message}")
