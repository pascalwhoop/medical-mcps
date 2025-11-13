"""
Base API Client - HTTP client with caching, rate limiting, and error handling.

Provides reusable base class for API clients with HTTP caching (hishel),
rate limiting via tenacity, standardized error handling, and async context manager support.
"""

import logging
import os
from abc import ABC
from pathlib import Path
from typing import Any

import httpx
from hishel import AsyncSqliteStorage
from hishel.httpx import AsyncCacheClient
from tenacity import retry, stop_after_attempt, wait_fixed

logger = logging.getLogger(__name__)

# Default cache directory - use per-process subdirectory to avoid SQLite locking issues
_process_id = os.getpid()
CACHE_DIR = (
    Path.home() / ".cache" / "medical-mcps" / "api_cache" / f"proc_{_process_id}"
)
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Cache TTL: 30 days in seconds
CACHE_TTL = 30 * 24 * 60 * 60


class BaseAPIClient(ABC):
    """
    Base class for API clients with HTTP caching, rate limiting, and error handling.

    Example:
        ```python
        class MyAPIClient(BaseAPIClient):
            def __init__(self):
                super().__init__(
                    base_url="https://api.example.com",
                    api_name="MyAPI",
                    rate_limit_delay=1.0,
                )

            async def get_data(self, id: str):
                return await self._request("GET", endpoint=f"/data/{id}")

        async with MyAPIClient() as client:
            data = await client.get_data("123")
        ```
    """

    def __init__(
        self,
        base_url: str,
        api_name: str,
        timeout: float = 30.0,
        rate_limit_delay: float | None = None,
        enable_cache: bool = True,
        cache_dir: Path | None = None,
    ):
        """Initialize base API client."""
        self.base_url = base_url
        self.api_name = api_name
        self.timeout = timeout
        self.rate_limit_delay = rate_limit_delay
        self.enable_cache = enable_cache
        self.cache_dir = cache_dir or CACHE_DIR
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self):
        """Async context manager entry - initialize HTTP client."""
        self._client = self._create_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - cleanup resources."""
        await self.close()

    @property
    def client(self) -> httpx.AsyncClient:
        """Get or create HTTP client (lazy initialization)."""
        if self._client is None:
            self._client = self._create_client()
        return self._client

    def _create_client(self) -> httpx.AsyncClient:
        """Create HTTP client (cached or regular). Falls back to non-cached on failure."""
        if self.enable_cache:
            try:
                storage = AsyncSqliteStorage(
                    database_path=str(self.cache_dir / f"{self.api_name.lower()}.db"),
                    default_ttl=CACHE_TTL,
                    refresh_ttl_on_access=True,
                )
                return AsyncCacheClient(
                    storage=storage,
                    timeout=self.timeout,
                    follow_redirects=True,
                )
            except Exception as e:
                logger.warning(
                    f"Failed to initialize cache for {self.api_name}: {e}. "
                    "Falling back to non-cached client."
                )
                return httpx.AsyncClient(timeout=self.timeout, follow_redirects=True)
        else:
            return httpx.AsyncClient(timeout=self.timeout, follow_redirects=True)

    def _is_cache_error(self, error: Exception) -> bool:
        """Check if exception is a cache database error."""
        if not self.enable_cache:
            return False
        if self._client is None or not isinstance(self._client, AsyncCacheClient):
            return False
        error_str = str(error).lower()
        return any(
            keyword in error_str
            for keyword in ["readonly", "database", "sqlite", "locked"]
        )

    async def _handle_cache_error_retry(self, request_func) -> Any:
        """Handle cache error by retrying request without cache."""
        logger.warning(
            f"Cache database error for {self.api_name}. Retrying request without cache."
        )
        try:
            if self._client:
                await self._client.aclose()
        except Exception:
            pass
        self._client = httpx.AsyncClient(timeout=self.timeout, follow_redirects=True)
        return await request_func()

    def _extract_error_message(self, error: httpx.HTTPStatusError) -> str:
        """Extract error message from HTTP status error response."""
        error_msg = f"{self.api_name} API error: HTTP {error.response.status_code}"
        try:
            error_detail = error.response.json()
            if isinstance(error_detail, dict):
                for field in ["error", "message", "detail", "error_message"]:
                    if field in error_detail:
                        error_msg += f" - {error_detail[field]}"
                        return error_msg
        except Exception:
            pass
        error_msg += f" - {str(error)}"
        return error_msg

    async def _request(
        self,
        method: str,
        endpoint: str | None = None,
        url: str | None = None,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
        form_data: dict[str, Any] | None = None,
        return_json: bool = True,
    ) -> dict[str, Any] | str:
        """
        Unified HTTP request method.

        Args:
            method: HTTP method ("GET" or "POST")
            endpoint: API endpoint relative to base_url (use either this or url)
            url: Full URL (use either this or endpoint)
            params: Query parameters
            json_data: JSON body data (for POST)
            form_data: Form body data (for POST)
            return_json: If True, return JSON dict; if False, return text

        Returns:
            Response as dict (if return_json=True) or str (if return_json=False)
        """
        # Build request URL
        if url:
            request_url = url
        elif endpoint:
            request_url = f"{self.base_url}{endpoint}"
        else:
            raise ValueError("Either endpoint or url must be provided")

        # Log request
        param_str = "&".join(f"{k}={v}" for k, v in (params or {}).items())
        log_url = f"{request_url}?{param_str}" if param_str else request_url
        logger.info(f"HTTP Request: {method} {log_url}")

        # Create request function
        async def make_request():
            if method == "GET":
                response = await self.client.get(request_url, params=params)
            elif method == "POST":
                if form_data is not None:
                    response = await self.client.post(
                        request_url, data=form_data, params=params
                    )
                else:
                    response = await self.client.post(
                        request_url, json=json_data, params=params
                    )
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            logger.info(
                f"HTTP Response: {response.status_code} {response.reason_phrase}"
            )
            return response.json() if return_json else response.text

        # Apply retry via tenacity if rate_limit_delay is configured (acts as delay between retries)
        request_func = make_request
        if self.rate_limit_delay:
            request_func = retry(
                stop=stop_after_attempt(3),
                wait=wait_fixed(self.rate_limit_delay),
                reraise=True,
            )(make_request)

        # Execute request with error handling
        try:
            return await request_func()
        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP Response: {e.response.status_code} {e.response.reason_phrase}"
            )
            raise Exception(self._extract_error_message(e)) from e
        except httpx.HTTPError as e:
            logger.error(f"HTTP Error: {str(e)}")
            raise Exception(f"{self.api_name} API error: {str(e)}") from e
        except Exception as e:
            if self._is_cache_error(e):
                return await self._handle_cache_error_retry(make_request)
            raise

    def format_response(
        self, data: dict | list | str, metadata: dict[str, Any] | None = None
    ) -> dict | list | str:
        """Format API response with optional metadata wrapper."""
        if metadata:
            return {"data": data, "metadata": metadata}
        return data

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
