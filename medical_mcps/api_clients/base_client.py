"""
Base API Client
Provides common HTTP client functionality and error handling for all API clients
"""

import asyncio
import logging
import time
from abc import ABC
from pathlib import Path
from typing import Any

import httpx
from hishel import AsyncSqliteStorage
from hishel.httpx import AsyncCacheClient

logger = logging.getLogger(__name__)

# Default cache directory
CACHE_DIR = Path.home() / ".cache" / "medical-mcps" / "api_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


class BaseAPIClient(ABC):
    """
    Base class for API clients with common functionality

    Features:
    - Standardized HTTP error handling
    - Async context manager support for resource cleanup
    - Optional rate limiting
    - Consistent response formatting
    - Transparent HTTP caching via hishel (RFC 9111 compliant)
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
        """
        Initialize base API client

        Args:
            base_url: Base URL for the API
            api_name: Name of the API (for error messages and response formatting)
            timeout: Request timeout in seconds
            rate_limit_delay: Minimum delay between requests in seconds (None = no rate limiting)
            enable_cache: Whether to enable HTTP caching (default: True)
            cache_dir: Custom cache directory (default: ~/.cache/ms-deep-dive/api_cache)
        """
        self.base_url = base_url
        self.api_name = api_name
        self.timeout = timeout
        self.rate_limit_delay = rate_limit_delay
        self.enable_cache = enable_cache
        self.cache_dir = cache_dir or CACHE_DIR
        self._client: httpx.AsyncClient | None = None
        self._last_request_time = 0.0

    async def __aenter__(self):
        """Async context manager entry"""
        if self.enable_cache:
            # Use hishel's AsyncCacheClient with SQLite storage
            storage = AsyncSqliteStorage(
                database_path=str(self.cache_dir / f"{self.api_name.lower()}.db"),
                default_ttl=2592000.0,  # 30 days = 30 * 24 * 60 * 60 seconds
                refresh_ttl_on_access=True,  # Reset TTL when accessing cached entries
            )
            self._client = AsyncCacheClient(
                storage=storage,
                timeout=self.timeout,
                follow_redirects=True,
            )
        else:
            # Use regular httpx client without caching
            self._client = httpx.AsyncClient(
                timeout=self.timeout, follow_redirects=True
            )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - cleanup resources"""
        if self._client:
            await self._client.aclose()
            self._client = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self._client is None:
            if self.enable_cache:
                storage = AsyncSqliteStorage(
                    database_path=str(self.cache_dir / f"{self.api_name.lower()}.db"),
                    default_ttl=2592000.0,  # 30 days
                    refresh_ttl_on_access=True,
                )
                self._client = AsyncCacheClient(
                    storage=storage,
                    timeout=self.timeout,
                    follow_redirects=True,
                )
            else:
                self._client = httpx.AsyncClient(
                    timeout=self.timeout, follow_redirects=True
                )
        return self._client

    async def _rate_limit(self):
        """Enforce rate limiting if configured"""
        if self.rate_limit_delay is None:
            return

        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < self.rate_limit_delay:
            await asyncio.sleep(self.rate_limit_delay - time_since_last)
        self._last_request_time = time.time()

    async def _get(
        self, endpoint: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Make a GET request to the API returning JSON

        Args:
            endpoint: API endpoint (will be appended to base_url)
            params: Query parameters

        Returns:
            JSON response as dict

        Raises:
            Exception: With descriptive error message if request fails
        """
        await self._rate_limit()
        url = f"{self.base_url}{endpoint}"

        # Log HTTP request
        param_str = "&".join(f"{k}={v}" for k, v in (params or {}).items())
        request_url = f"{url}?{param_str}" if param_str else url
        logger.info(f"HTTP Request: GET {request_url}")

        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            logger.info(
                f"HTTP Response: {response.status_code} {response.reason_phrase}"
            )
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP Response: {e.response.status_code} {e.response.reason_phrase}"
            )
            # Extract detailed error information
            error_msg = f"{self.api_name} API error: HTTP {e.response.status_code}"
            try:
                error_detail = e.response.json()
                if isinstance(error_detail, dict):
                    # Try common error message fields
                    for field in ["error", "message", "detail", "error_message"]:
                        if field in error_detail:
                            error_msg += f" - {error_detail[field]}"
                            break
                    else:
                        error_msg += f" - {str(e)}"
            except Exception:
                error_msg += f" - {str(e)}"
            raise Exception(error_msg) from e
        except httpx.HTTPError as e:
            logger.error(f"HTTP Error: {str(e)}")
            raise Exception(f"{self.api_name} API error: {str(e)}") from e

    async def _get_text(
        self, endpoint: str, params: dict[str, Any] | None = None
    ) -> str:
        """
        Make a GET request to the API returning text

        Args:
            endpoint: API endpoint (will be appended to base_url)
            params: Query parameters

        Returns:
            Response text

        Raises:
            Exception: With descriptive error message if request fails
        """
        await self._rate_limit()
        url = f"{self.base_url}{endpoint}"

        # Log HTTP request
        param_str = "&".join(f"{k}={v}" for k, v in (params or {}).items())
        request_url = f"{url}?{param_str}" if param_str else url
        logger.info(f"HTTP Request: GET {request_url}")

        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            logger.info(
                f"HTTP Response: {response.status_code} {response.reason_phrase}"
            )
            return response.text
        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP Response: {e.response.status_code} {e.response.reason_phrase}"
            )
            error_msg = (
                f"{self.api_name} API error: HTTP {e.response.status_code} - {str(e)}"
            )
            raise Exception(error_msg) from e
        except httpx.HTTPError as e:
            logger.error(f"HTTP Error: {str(e)}")
            raise Exception(f"{self.api_name} API error: {str(e)}") from e

    async def _get_text_direct(
        self, url: str, params: dict[str, Any] | None = None
    ) -> str:
        """
        Make a GET request to a full URL (not relative to base_url) returning text.
        Useful for endpoints that return non-JSON formats (FASTA, XML, etc.)

        Args:
            url: Full URL to request
            params: Query parameters

        Returns:
            Response text

        Raises:
            Exception: With descriptive error message if request fails
        """
        await self._rate_limit()

        # Log HTTP request
        param_str = "&".join(f"{k}={v}" for k, v in (params or {}).items())
        request_url = f"{url}?{param_str}" if param_str else url
        logger.info(f"HTTP Request: GET {request_url}")

        try:
            response = await self.client.get(url, params=params, follow_redirects=True)
            response.raise_for_status()
            logger.info(
                f"HTTP Response: {response.status_code} {response.reason_phrase}"
            )
            return response.text
        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP Response: {e.response.status_code} {e.response.reason_phrase}"
            )
            error_msg = (
                f"{self.api_name} API error: HTTP {e.response.status_code} - {str(e)}"
            )
            raise Exception(error_msg) from e
        except httpx.HTTPError as e:
            logger.error(f"HTTP Error: {str(e)}")
            raise Exception(f"{self.api_name} API error: {str(e)}") from e

    async def _post(
        self,
        endpoint: str,
        json_data: dict[str, Any] | None = None,
        form_data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Make a POST request to the API

        Args:
            endpoint: API endpoint (will be appended to base_url)
            json_data: JSON data to send in body (use either this or form_data)
            form_data: Form data to send (use either this or json_data)
            params: Query parameters

        Returns:
            JSON response as dict

        Raises:
            Exception: With descriptive error message if request fails
        """
        await self._rate_limit()
        url = f"{self.base_url}{endpoint}"

        # Log HTTP request
        param_str = "&".join(f"{k}={v}" for k, v in (params or {}).items())
        request_url = f"{url}?{param_str}" if param_str else url
        logger.info(f"HTTP Request: POST {request_url}")

        try:
            if form_data is not None:
                response = await self.client.post(url, data=form_data, params=params)
            else:
                response = await self.client.post(url, json=json_data, params=params)
            response.raise_for_status()
            logger.info(
                f"HTTP Response: {response.status_code} {response.reason_phrase}"
            )
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP Response: {e.response.status_code} {e.response.reason_phrase}"
            )
            error_msg = f"{self.api_name} API error: HTTP {e.response.status_code}"
            try:
                error_detail = e.response.json()
                if isinstance(error_detail, dict):
                    for field in ["error", "message", "detail", "error_message"]:
                        if field in error_detail:
                            error_msg += f" - {error_detail[field]}"
                            break
                    else:
                        error_msg += f" - {str(e)}"
            except Exception:
                error_msg += f" - {str(e)}"
            raise Exception(error_msg) from e
        except httpx.HTTPError as e:
            logger.error(f"HTTP Error: {str(e)}")
            raise Exception(f"{self.api_name} API error: {str(e)}") from e

    def format_response(
        self, data: dict | list | str, metadata: dict[str, Any] | None = None
    ) -> dict | list | str:
        """
        Format API response with consistent structure

        Args:
            data: Response data (dict/list will be returned as structured data, str will be used as-is)
            metadata: Optional metadata to include (e.g., result count, timestamp)

        Returns:
            Structured response (dict/list/str). If metadata is provided, returns dict with
            'data' and 'metadata' keys. Otherwise returns data as-is.
        """
        # If metadata is provided, wrap in structured format
        if metadata:
            return {
                "data": data,
                "metadata": metadata,
            }

        # Otherwise return data as-is (dict, list, or str)
        return data

    async def close(self):
        """Close the HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None
