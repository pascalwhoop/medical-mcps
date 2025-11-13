"""Tests for BaseAPIClient with mocked HTTP/IO/cache operations"""

import asyncio
import logging
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from hishel.httpx import AsyncCacheClient

from medical_mcps.api_clients.base_client import BaseAPIClient

# Disable logging during tests
logging.getLogger("medical_mcps.api_clients.base_client").setLevel(logging.CRITICAL)


class ConcreteAPIClient(BaseAPIClient):
    """Concrete implementation for testing"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class TestBaseAPIClientInitialization:
    """Test client initialization"""

    def test_init_with_defaults(self):
        """Test initialization with default parameters"""
        client = ConcreteAPIClient(
            base_url="https://api.example.com", api_name="TestAPI"
        )
        assert client.base_url == "https://api.example.com"
        assert client.api_name == "TestAPI"
        assert client.timeout == 30.0
        assert client.rate_limit_delay is None
        assert client.enable_cache is True
        assert client._client is None

    def test_init_with_custom_params(self):
        """Test initialization with custom parameters"""
        cache_dir = Path("/tmp/test_cache")
        client = ConcreteAPIClient(
            base_url="https://api.example.com",
            api_name="TestAPI",
            timeout=60.0,
            rate_limit_delay=1.0,
            enable_cache=False,
            cache_dir=cache_dir,
        )
        assert client.timeout == 60.0
        assert client.rate_limit_delay == 1.0
        assert client.enable_cache is False
        assert client.cache_dir == cache_dir


class TestBaseAPIClientContextManager:
    """Test async context manager functionality"""

    @pytest.mark.asyncio
    async def test_context_manager_with_cache_enabled(self):
        """Test context manager with cache enabled"""
        with (
            patch(
                "medical_mcps.api_clients.base_client.AsyncSqliteStorage"
            ) as mock_storage,
            patch(
                "medical_mcps.api_clients.base_client.AsyncCacheClient"
            ) as mock_cache_client,
        ):
            mock_storage_instance = MagicMock()
            mock_storage.return_value = mock_storage_instance
            mock_client_instance = AsyncMock()
            mock_cache_client.return_value = mock_client_instance

            async with ConcreteAPIClient(
                base_url="https://api.example.com",
                api_name="TestAPI",
                enable_cache=True,
            ) as client:
                assert client._client is not None
                assert client._client == mock_client_instance
                mock_cache_client.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager_with_cache_disabled(self):
        """Test context manager with cache disabled"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value = mock_client_instance

            async with ConcreteAPIClient(
                base_url="https://api.example.com",
                api_name="TestAPI",
                enable_cache=False,
            ) as client:
                assert client._client is not None
                assert client._client == mock_client_instance
                mock_client.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager_cache_fallback(self):
        """Test context manager falls back to non-cached client on cache init failure"""
        with (
            patch(
                "medical_mcps.api_clients.base_client.AsyncSqliteStorage"
            ) as mock_storage,
            patch("httpx.AsyncClient") as mock_client,
        ):
            mock_storage.side_effect = Exception("Database locked")
            mock_client_instance = AsyncMock()
            mock_client.return_value = mock_client_instance

            async with ConcreteAPIClient(
                base_url="https://api.example.com",
                api_name="TestAPI",
                enable_cache=True,
            ) as client:
                assert client._client is not None
                assert client._client == mock_client_instance
                mock_client.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager_cleanup(self):
        """Test context manager properly cleans up resources"""
        mock_client_instance = AsyncMock()
        with patch("httpx.AsyncClient", return_value=mock_client_instance):
            async with ConcreteAPIClient(
                base_url="https://api.example.com",
                api_name="TestAPI",
                enable_cache=False,
            ) as client:
                assert client._client is not None

            # After exiting context, client should be closed
            mock_client_instance.aclose.assert_called_once()
            assert client._client is None


class TestBaseAPIClientProperty:
    """Test client property lazy initialization"""

    @pytest.mark.asyncio
    async def test_client_property_lazy_init_with_cache(self):
        """Test client property lazy initialization with cache"""
        with (
            patch(
                "medical_mcps.api_clients.base_client.AsyncSqliteStorage"
            ) as mock_storage,
            patch(
                "medical_mcps.api_clients.base_client.AsyncCacheClient"
            ) as mock_cache_client,
        ):
            mock_storage_instance = MagicMock()
            mock_storage.return_value = mock_storage_instance
            mock_client_instance = AsyncMock()
            mock_cache_client.return_value = mock_client_instance

            client = ConcreteAPIClient(
                base_url="https://api.example.com",
                api_name="TestAPI",
                enable_cache=True,
            )
            assert client._client is None

            # Accessing property should initialize client
            accessed_client = client.client
            assert accessed_client == mock_client_instance
            assert client._client == mock_client_instance
            mock_cache_client.assert_called_once()

    @pytest.mark.asyncio
    async def test_client_property_lazy_init_without_cache(self):
        """Test client property lazy initialization without cache"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value = mock_client_instance

            client = ConcreteAPIClient(
                base_url="https://api.example.com",
                api_name="TestAPI",
                enable_cache=False,
            )
            assert client._client is None

            # Accessing property should initialize client
            accessed_client = client.client
            assert accessed_client == mock_client_instance
            assert client._client == mock_client_instance
            mock_client.assert_called_once()

    @pytest.mark.asyncio
    async def test_client_property_cache_fallback(self):
        """Test client property falls back on cache init failure"""
        with (
            patch(
                "medical_mcps.api_clients.base_client.AsyncSqliteStorage"
            ) as mock_storage,
            patch("httpx.AsyncClient") as mock_client,
        ):
            mock_storage.side_effect = Exception("Database readonly")
            mock_client_instance = AsyncMock()
            mock_client.return_value = mock_client_instance

            client = ConcreteAPIClient(
                base_url="https://api.example.com",
                api_name="TestAPI",
                enable_cache=True,
            )
            accessed_client = client.client
            assert accessed_client == mock_client_instance
            mock_client.assert_called_once()


class TestBaseAPIClientRateLimiting:
    """Test rate limiting functionality"""

    @pytest.mark.asyncio
    async def test_rate_limiting_configured(self):
        """Test that rate_limit_delay is stored (tenacity handles retries, not rate limiting)"""
        client = ConcreteAPIClient(
            base_url="https://api.example.com",
            api_name="TestAPI",
            rate_limit_delay=0.1,
            enable_cache=False,
        )
        assert client.rate_limit_delay == 0.1
        # Note: tenacity is used for retries with delays, not rate limiting between all requests

    @pytest.mark.asyncio
    async def test_rate_limiting_disabled(self):
        """Test rate limiting is not enforced when disabled"""
        client = ConcreteAPIClient(
            base_url="https://api.example.com",
            api_name="TestAPI",
            rate_limit_delay=None,
            enable_cache=False,
        )
        mock_client = AsyncMock()
        client._client = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.reason_phrase = "OK"
        mock_response.json.return_value = {"data": "test"}
        mock_client.get.return_value = mock_response

        start_time = asyncio.get_event_loop().time()
        await client._request("GET", endpoint="/test")
        await client._request("GET", endpoint="/test")
        duration = asyncio.get_event_loop().time() - start_time

        # Should be fast (no delay)
        assert duration < 0.1


class TestBaseAPIClientRequest:
    """Test _request method"""

    @pytest.mark.asyncio
    async def test_request_get_json_success(self):
        """Test successful GET request returning JSON"""
        client = ConcreteAPIClient(
            base_url="https://api.example.com", api_name="TestAPI", enable_cache=False
        )
        mock_client = AsyncMock()
        client._client = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.reason_phrase = "OK"
        mock_response.json.return_value = {"data": "test"}
        mock_client.get.return_value = mock_response

        result = await client._request("GET", endpoint="/test", params={"key": "value"})
        assert result == {"data": "test"}
        mock_client.get.assert_called_once_with(
            "https://api.example.com/test", params={"key": "value"}
        )

    @pytest.mark.asyncio
    async def test_request_http_status_error(self):
        """Test request with HTTP status error"""
        client = ConcreteAPIClient(
            base_url="https://api.example.com", api_name="TestAPI", enable_cache=False
        )
        mock_client = AsyncMock()
        client._client = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.reason_phrase = "Not Found"
        mock_response.json.return_value = {"error": "Resource not found"}

        error = httpx.HTTPStatusError(
            "Not Found", request=MagicMock(), response=mock_response
        )
        mock_client.get.side_effect = error

        with pytest.raises(Exception) as exc_info:
            await client._request("GET", endpoint="/test")
        assert "TestAPI API error: HTTP 404" in str(exc_info.value)
        assert "Resource not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_request_http_error(self):
        """Test request with HTTP error"""
        client = ConcreteAPIClient(
            base_url="https://api.example.com", api_name="TestAPI", enable_cache=False
        )
        mock_client = AsyncMock()
        client._client = mock_client

        error = httpx.HTTPError("Connection failed")
        mock_client.get.side_effect = error

        with pytest.raises(Exception) as exc_info:
            await client._request("GET", endpoint="/test")
        assert "TestAPI API error: Connection failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_request_cache_error_retry(self):
        """Test request retries without cache on cache error"""
        client = ConcreteAPIClient(
            base_url="https://api.example.com", api_name="TestAPI", enable_cache=True
        )
        mock_cache_client = AsyncMock(spec=AsyncCacheClient)
        client._client = mock_cache_client

        # First call raises cache error
        cache_error = Exception("database is locked")
        mock_cache_client.get.side_effect = cache_error

        # Mock successful retry
        mock_regular_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.reason_phrase = "OK"
        mock_response.json.return_value = {"data": "retry_success"}
        mock_regular_client.get.return_value = mock_response

        with patch("httpx.AsyncClient", return_value=mock_regular_client):
            result = await client._request("GET", endpoint="/test")

        assert result == {"data": "retry_success"}
        # Verify that the cached client was closed and replaced
        mock_cache_client.aclose.assert_called_once()
        # Verify that the new client is not a cached client
        assert client._client == mock_regular_client
        assert not isinstance(client._client, AsyncCacheClient)

    @pytest.mark.asyncio
    async def test_request_get_text_success(self):
        """Test successful GET request returning text"""
        client = ConcreteAPIClient(
            base_url="https://api.example.com", api_name="TestAPI", enable_cache=False
        )
        mock_client = AsyncMock()
        client._client = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.reason_phrase = "OK"
        mock_response.text = "text content"
        mock_client.get.return_value = mock_response

        result = await client._request("GET", endpoint="/test", return_json=False)
        assert result == "text content"

    @pytest.mark.asyncio
    async def test_request_get_text_direct_success(self):
        """Test successful GET request to full URL returning text"""
        client = ConcreteAPIClient(
            base_url="https://api.example.com", api_name="TestAPI", enable_cache=False
        )
        mock_client = AsyncMock()
        client._client = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.reason_phrase = "OK"
        mock_response.text = "direct text content"
        mock_client.get.return_value = mock_response

        result = await client._request(
            "GET", url="https://external.com/data", return_json=False
        )
        assert result == "direct text content"
        mock_client.get.assert_called_once_with(
            "https://external.com/data", params=None
        )

    @pytest.mark.asyncio
    async def test_request_caching_stores_response(self):
        """Test that cache client stores responses on first request"""
        client = ConcreteAPIClient(
            base_url="https://api.example.com", api_name="TestAPI", enable_cache=True
        )
        mock_cache_client = AsyncMock(spec=AsyncCacheClient)
        client._client = mock_cache_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.reason_phrase = "OK"
        mock_response.json.return_value = {"data": "cached"}
        mock_response.extensions = {
            "hishel_stored": True,
            "hishel_from_cache": False,
        }
        mock_cache_client.get.return_value = mock_response

        # First request - should store in cache
        result = await client._request("GET", endpoint="/test")
        assert result == {"data": "cached"}
        assert mock_cache_client.get.call_count == 1
        # Verify cache client was used (not regular client)
        assert isinstance(client._client, AsyncCacheClient)

    @pytest.mark.asyncio
    async def test_request_cache_vs_no_cache(self):
        """Test that cache-enabled client uses AsyncCacheClient vs regular client"""
        # With cache enabled
        cached_client = ConcreteAPIClient(
            base_url="https://api.example.com", api_name="TestAPI", enable_cache=True
        )
        with (
            patch(
                "medical_mcps.api_clients.base_client.AsyncSqliteStorage"
            ) as mock_storage,
            patch(
                "medical_mcps.api_clients.base_client.AsyncCacheClient"
            ) as mock_cache_client,
        ):
            mock_storage_instance = MagicMock()
            mock_storage.return_value = mock_storage_instance
            mock_cache_instance = AsyncMock(spec=AsyncCacheClient)
            mock_cache_client.return_value = mock_cache_instance

            async with cached_client as client:
                assert isinstance(client._client, AsyncCacheClient)

        # With cache disabled
        non_cached_client = ConcreteAPIClient(
            base_url="https://api.example.com", api_name="TestAPI", enable_cache=False
        )
        with patch("httpx.AsyncClient") as mock_regular_client:
            mock_regular_instance = AsyncMock()
            mock_regular_client.return_value = mock_regular_instance

            async with non_cached_client as client:
                assert not isinstance(client._client, AsyncCacheClient)
                # With cache disabled, should use regular httpx.AsyncClient (mocked here)
                assert client._client == mock_regular_instance

    @pytest.mark.asyncio
    async def test_request_post_json_success(self):
        """Test successful POST request with JSON"""
        client = ConcreteAPIClient(
            base_url="https://api.example.com", api_name="TestAPI", enable_cache=False
        )
        mock_client = AsyncMock()
        client._client = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.reason_phrase = "OK"
        mock_response.json.return_value = {"result": "success"}
        mock_client.post.return_value = mock_response

        result = await client._request(
            "POST", endpoint="/test", json_data={"key": "value"}
        )
        assert result == {"result": "success"}
        mock_client.post.assert_called_once_with(
            "https://api.example.com/test", json={"key": "value"}, params=None
        )

    @pytest.mark.asyncio
    async def test_request_post_form_success(self):
        """Test successful POST request with form data"""
        client = ConcreteAPIClient(
            base_url="https://api.example.com", api_name="TestAPI", enable_cache=False
        )
        mock_client = AsyncMock()
        client._client = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.reason_phrase = "OK"
        mock_response.json.return_value = {"result": "success"}
        mock_client.post.return_value = mock_response

        result = await client._request(
            "POST", endpoint="/test", form_data={"key": "value"}
        )
        assert result == {"result": "success"}
        mock_client.post.assert_called_once_with(
            "https://api.example.com/test", data={"key": "value"}, params=None
        )

    @pytest.mark.asyncio
    async def test_request_post_error(self):
        """Test POST request with error"""
        client = ConcreteAPIClient(
            base_url="https://api.example.com", api_name="TestAPI", enable_cache=False
        )
        mock_client = AsyncMock()
        client._client = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.reason_phrase = "Bad Request"
        mock_response.json.return_value = {"error": "Invalid input"}

        error = httpx.HTTPStatusError(
            "Bad Request", request=MagicMock(), response=mock_response
        )
        mock_client.post.side_effect = error

        with pytest.raises(Exception) as exc_info:
            await client._request("POST", endpoint="/test", json_data={"key": "value"})
        assert "TestAPI API error: HTTP 400" in str(exc_info.value)
        assert "Invalid input" in str(exc_info.value)


class TestBaseAPIClientFormatResponse:
    """Test format_response method"""

    def test_format_response_with_metadata(self):
        """Test formatting response with metadata"""
        client = ConcreteAPIClient(
            base_url="https://api.example.com", api_name="TestAPI"
        )
        result = client.format_response({"data": "test"}, metadata={"count": 1})
        assert result == {"data": {"data": "test"}, "metadata": {"count": 1}}

    def test_format_response_without_metadata(self):
        """Test formatting response without metadata"""
        client = ConcreteAPIClient(
            base_url="https://api.example.com", api_name="TestAPI"
        )
        result = client.format_response({"data": "test"})
        assert result == {"data": "test"}

    def test_format_response_list(self):
        """Test formatting list response"""
        client = ConcreteAPIClient(
            base_url="https://api.example.com", api_name="TestAPI"
        )
        result = client.format_response([1, 2, 3])
        assert result == [1, 2, 3]

    def test_format_response_string(self):
        """Test formatting string response"""
        client = ConcreteAPIClient(
            base_url="https://api.example.com", api_name="TestAPI"
        )
        result = client.format_response("text")
        assert result == "text"


class TestBaseAPIClientClose:
    """Test close method"""

    @pytest.mark.asyncio
    async def test_close(self):
        """Test closing client"""
        client = ConcreteAPIClient(
            base_url="https://api.example.com", api_name="TestAPI", enable_cache=False
        )
        mock_client = AsyncMock()
        client._client = mock_client

        await client.close()
        mock_client.aclose.assert_called_once()
        assert client._client is None

    @pytest.mark.asyncio
    async def test_close_no_client(self):
        """Test closing when no client exists"""
        client = ConcreteAPIClient(
            base_url="https://api.example.com", api_name="TestAPI"
        )
        await client.close()  # Should not raise
        assert client._client is None
