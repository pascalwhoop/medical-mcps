"""Tests for BaseAPIClient with mocked HTTP/IO/cache operations"""

import asyncio
import logging
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from hishel.httpx import AsyncCacheClient

from medical_mcps.api_clients.base_client import APINotFoundError, APIUpstreamError, BaseAPIClient

# Disable logging during tests
logging.getLogger("medical_mcps.api_clients.base_client").setLevel(logging.CRITICAL)


class ConcreteAPIClient(BaseAPIClient):
    """Concrete implementation for testing"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


# Test fixtures and helpers
@pytest.fixture
def base_url():
    """Base URL for test clients"""
    return "https://api.example.com"


@pytest.fixture
def api_name():
    """API name for test clients"""
    return "TestAPI"


@pytest.fixture
def mock_response():
    """Factory fixture for creating mock HTTP responses"""

    def _create_response(
        status_code=200,
        reason_phrase="OK",
        json_data=None,
        text=None,
        extensions=None,
    ):
        response = MagicMock()
        response.status_code = status_code
        response.reason_phrase = reason_phrase
        if json_data is not None:
            response.json.return_value = json_data
        if text is not None:
            response.text = text
        if extensions:
            response.extensions = extensions
        return response

    return _create_response


@pytest.fixture
def mock_client():
    """Create a mock HTTP client"""
    return AsyncMock()


class TestBaseAPIClientInitialization:
    """Test client initialization"""

    def test_init_with_defaults(self, base_url, api_name):
        client = ConcreteAPIClient(base_url=base_url, api_name=api_name, enable_cache=False)
        assert client.base_url == base_url
        assert client.api_name == api_name
        assert client.timeout == 30.0
        assert client.rate_limit_delay is None
        assert client._client is None

    def test_init_with_custom_params(self, base_url, api_name):
        """Test initialization with custom parameters"""
        cache_dir = Path("/tmp/test_cache")
        client = ConcreteAPIClient(
            base_url=base_url,
            api_name=api_name,
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
    async def test_context_manager_with_cache_enabled(self, base_url, api_name):
        """Test context manager with cache enabled"""
        with (
            patch("medical_mcps.api_clients.base_client.AsyncSqliteStorage") as mock_storage,
            patch("medical_mcps.api_clients.base_client.AsyncCacheClient") as mock_cache_client,
        ):
            mock_storage_instance = MagicMock()
            mock_storage.return_value = mock_storage_instance
            mock_client_instance = AsyncMock()
            mock_cache_client.return_value = mock_client_instance

            async with ConcreteAPIClient(
                base_url=base_url, api_name=api_name, enable_cache=True
            ) as client:
                assert client._client is not None
                assert client._client == mock_client_instance
                mock_cache_client.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager_with_cache_disabled(self, base_url, api_name):
        """Test context manager with cache disabled"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value = mock_client_instance

            async with ConcreteAPIClient(
                base_url=base_url, api_name=api_name, enable_cache=False
            ) as client:
                assert client._client is not None
                assert client._client == mock_client_instance
                mock_client.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager_cache_fallback(self, base_url, api_name):
        """Test context manager falls back to non-cached client on cache init failure"""
        with (
            patch("medical_mcps.api_clients.base_client.AsyncSqliteStorage") as mock_storage,
            patch("httpx.AsyncClient") as mock_client,
        ):
            mock_storage.side_effect = Exception("Database locked")
            mock_client_instance = AsyncMock()
            mock_client.return_value = mock_client_instance

            async with ConcreteAPIClient(
                base_url=base_url, api_name=api_name, enable_cache=True
            ) as client:
                assert client._client is not None
                assert client._client == mock_client_instance
                mock_client.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager_cleanup(self, base_url, api_name):
        """Test context manager properly cleans up resources"""
        mock_client_instance = AsyncMock()
        with patch("httpx.AsyncClient", return_value=mock_client_instance):
            async with ConcreteAPIClient(
                base_url=base_url, api_name=api_name, enable_cache=False
            ) as client:
                assert client._client is not None

            # After exiting context, client should be closed
            mock_client_instance.aclose.assert_called_once()
            assert client._client is None


class TestBaseAPIClientProperty:
    """Test client property lazy initialization"""

    @pytest.mark.asyncio
    async def test_client_property_lazy_init_with_cache(self, base_url, api_name):
        """Test client property lazy initialization with cache"""
        with (
            patch("medical_mcps.api_clients.base_client.AsyncSqliteStorage") as mock_storage,
            patch("medical_mcps.api_clients.base_client.AsyncCacheClient") as mock_cache_client,
        ):
            mock_storage_instance = MagicMock()
            mock_storage.return_value = mock_storage_instance
            mock_client_instance = AsyncMock()
            mock_cache_client.return_value = mock_client_instance

            client = ConcreteAPIClient(base_url=base_url, api_name=api_name, enable_cache=True)
            assert client._client is None

            # Accessing property should initialize client
            accessed_client = client.client
            assert accessed_client == mock_client_instance
            assert client._client == mock_client_instance
            mock_cache_client.assert_called_once()

    @pytest.mark.asyncio
    async def test_client_property_lazy_init_without_cache(self, base_url, api_name):
        """Test client property lazy initialization without cache"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value = mock_client_instance

            client = ConcreteAPIClient(base_url=base_url, api_name=api_name, enable_cache=False)
            assert client._client is None

            # Accessing property should initialize client
            accessed_client = client.client
            assert accessed_client == mock_client_instance
            assert client._client == mock_client_instance
            mock_client.assert_called_once()

    @pytest.mark.asyncio
    async def test_client_property_cache_fallback(self, base_url, api_name):
        """Test client property falls back on cache init failure"""
        with (
            patch("medical_mcps.api_clients.base_client.AsyncSqliteStorage") as mock_storage,
            patch("httpx.AsyncClient") as mock_client,
        ):
            mock_storage.side_effect = Exception("Database readonly")
            mock_client_instance = AsyncMock()
            mock_client.return_value = mock_client_instance

            client = ConcreteAPIClient(base_url=base_url, api_name=api_name, enable_cache=True)
            accessed_client = client.client
            assert accessed_client == mock_client_instance
            mock_client.assert_called_once()


class TestBaseAPIClientRateLimiting:
    """Test rate limiting functionality"""

    def test_rate_limiting_configured(self, base_url, api_name):
        """Test that rate_limit_delay is stored"""
        client = ConcreteAPIClient(
            base_url=base_url,
            api_name=api_name,
            rate_limit_delay=0.1,
            enable_cache=False,
        )
        assert client.rate_limit_delay == 0.1

    @pytest.mark.asyncio
    async def test_rate_limiting_disabled(self, base_url, api_name, mock_response):
        """Test rate limiting is not enforced when disabled"""
        client = ConcreteAPIClient(
            base_url=base_url,
            api_name=api_name,
            rate_limit_delay=None,
            enable_cache=False,
        )
        mock_client = AsyncMock()
        client._client = mock_client

        mock_client.get.return_value = mock_response(json_data={"data": "test"})

        start_time = asyncio.get_event_loop().time()
        await client._request("GET", endpoint="/test")
        await client._request("GET", endpoint="/test")
        duration = asyncio.get_event_loop().time() - start_time

        # Should be fast (no delay)
        assert duration < 0.1


class TestBaseAPIClientRequest:
    """Test _request method"""

    @pytest.fixture
    def client(self, base_url, api_name):
        """Create a test client with cache disabled"""
        return ConcreteAPIClient(base_url=base_url, api_name=api_name, enable_cache=False)

    @pytest.mark.asyncio
    async def test_request_get_json_success(self, client, mock_response):
        """Test successful GET request returning JSON"""
        mock_client = AsyncMock()
        client._client = mock_client
        mock_client.get.return_value = mock_response(json_data={"data": "test"})

        result = await client._request("GET", endpoint="/test", params={"key": "value"})
        assert result == {"data": "test"}
        mock_client.get.assert_called_once_with(
            "https://api.example.com/test", params={"key": "value"}, timeout=None
        )

    @pytest.mark.asyncio
    async def test_request_http_status_error_not_found(self, client, mock_response):
        """404 responses raise APINotFoundError."""
        mock_client = AsyncMock()
        client._client = mock_client
        error = httpx.HTTPStatusError(
            "Not Found",
            request=MagicMock(),
            response=mock_response(
                status_code=404,
                reason_phrase="Not Found",
                json_data={"error": "Resource not found"},
            ),
        )
        mock_client.get.side_effect = error

        with pytest.raises(APINotFoundError) as exc_info:
            await client._request("GET", endpoint="/test")
        assert "TestAPI API error: HTTP 404" in str(exc_info.value)
        assert "Resource not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_request_http_status_error_bad_request(self, client, mock_response):
        """Non-404 HTTP errors still raise generic Exception."""
        mock_client = AsyncMock()
        client._client = mock_client
        error = httpx.HTTPStatusError(
            "Bad Request",
            request=MagicMock(),
            response=mock_response(
                status_code=400,
                reason_phrase="Bad Request",
                json_data={"error": "Invalid input"},
            ),
        )
        mock_client.get.side_effect = error

        with pytest.raises(Exception) as exc_info:
            await client._request("GET", endpoint="/test")
        assert "TestAPI API error: HTTP 400" in str(exc_info.value)
        assert "Invalid input" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_request_http_status_error_upstream(self, client, mock_response):
        """5xx responses raise APIUpstreamError."""
        mock_client = AsyncMock()
        client._client = mock_client
        error = httpx.HTTPStatusError(
            "Bad Gateway",
            request=MagicMock(),
            response=mock_response(
                status_code=502,
                reason_phrase="Bad Gateway",
                json_data={"error": "upstream down"},
            ),
        )
        mock_client.get.side_effect = error

        with pytest.raises(APIUpstreamError) as exc_info:
            await client._request("GET", endpoint="/test")
        assert exc_info.value.status_code == 502
        assert "TestAPI API error: HTTP 502" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_request_http_error(self, client):
        """Test request with HTTP error"""
        mock_client = AsyncMock()
        client._client = mock_client

        error = httpx.HTTPError("Connection failed")
        mock_client.get.side_effect = error

        with pytest.raises(Exception) as exc_info:
            await client._request("GET", endpoint="/test")
        assert "TestAPI API error: Connection failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_request_cache_error_retry(self, base_url, api_name, mock_response):
        """Test request retries without cache on cache error"""
        client = ConcreteAPIClient(base_url=base_url, api_name=api_name, enable_cache=True)
        mock_cache_client = AsyncMock(spec=AsyncCacheClient)
        client._client = mock_cache_client

        # First call raises cache error
        mock_cache_client.get.side_effect = Exception("database is locked")

        # Mock successful retry
        mock_regular_client = AsyncMock()
        mock_regular_client.get.return_value = mock_response(json_data={"data": "retry_success"})

        with patch("httpx.AsyncClient", return_value=mock_regular_client):
            result = await client._request("GET", endpoint="/test")

        assert result == {"data": "retry_success"}
        # Verify that the cached client was closed and replaced
        mock_cache_client.aclose.assert_called_once()
        # Verify that the new client is not a cached client
        assert client._client == mock_regular_client
        assert not isinstance(client._client, AsyncCacheClient)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "return_json,expected_result",
        [(True, {"data": "test"}), (False, "text content")],
    )
    async def test_request_get_text_success(
        self, client, mock_response, return_json, expected_result
    ):
        """Test successful GET request returning JSON or text"""
        mock_client = AsyncMock()
        client._client = mock_client

        if return_json:
            mock_client.get.return_value = mock_response(json_data={"data": "test"})
        else:
            mock_client.get.return_value = mock_response(text="text content")

        result = await client._request("GET", endpoint="/test", return_json=return_json)
        assert result == expected_result

    @pytest.mark.asyncio
    async def test_request_get_text_direct_success(self, client, mock_response):
        """Test successful GET request to full URL returning text"""
        mock_client = AsyncMock()
        client._client = mock_client
        mock_client.get.return_value = mock_response(text="direct text content")

        result = await client._request("GET", url="https://external.com/data", return_json=False)
        assert result == "direct text content"
        mock_client.get.assert_called_once_with(
            "https://external.com/data", params=None, timeout=None
        )

    @pytest.mark.asyncio
    async def test_request_caching_stores_response(self, base_url, api_name, mock_response):
        """Test that cache client stores responses on first request"""
        client = ConcreteAPIClient(base_url=base_url, api_name=api_name, enable_cache=True)
        mock_cache_client = AsyncMock(spec=AsyncCacheClient)
        client._client = mock_cache_client

        mock_cache_client.get.return_value = mock_response(
            json_data={"data": "cached"},
            extensions={
                "hishel_stored": True,
                "hishel_from_cache": False,
            },
        )

        # First request - should store in cache
        result = await client._request("GET", endpoint="/test")
        assert result == {"data": "cached"}
        assert mock_cache_client.get.call_count == 1
        # Verify cache client was used (not regular client)
        assert isinstance(client._client, AsyncCacheClient)

    @pytest.mark.asyncio
    async def test_request_cache_vs_no_cache(self, base_url, api_name):
        """Test that cache-enabled client uses AsyncCacheClient vs regular client"""
        # With cache enabled
        cached_client = ConcreteAPIClient(base_url=base_url, api_name=api_name, enable_cache=True)
        with (
            patch("medical_mcps.api_clients.base_client.AsyncSqliteStorage") as mock_storage,
            patch("medical_mcps.api_clients.base_client.AsyncCacheClient") as mock_cache_client,
        ):
            mock_storage_instance = MagicMock()
            mock_storage.return_value = mock_storage_instance
            mock_cache_instance = AsyncMock(spec=AsyncCacheClient)
            mock_cache_client.return_value = mock_cache_instance

            async with cached_client as client:
                assert isinstance(client._client, AsyncCacheClient)

        # With cache disabled
        non_cached_client = ConcreteAPIClient(
            base_url=base_url, api_name=api_name, enable_cache=False
        )
        with patch("httpx.AsyncClient") as mock_regular_client:
            mock_regular_instance = AsyncMock()
            mock_regular_client.return_value = mock_regular_instance

            async with non_cached_client as client:
                assert not isinstance(client._client, AsyncCacheClient)
                # With cache disabled, should use regular httpx.AsyncClient (mocked here)
                assert client._client == mock_regular_instance

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "method,data_param,data_value,expected_call_kwargs",
        [
            (
                "POST",
                "json_data",
                {"key": "value"},
                {"json": {"key": "value"}, "params": None, "timeout": None},
            ),
            (
                "POST",
                "form_data",
                {"key": "value"},
                {"data": {"key": "value"}, "params": None, "timeout": None},
            ),
        ],
    )
    async def test_request_post_success(
        self,
        client,
        mock_response,
        method,
        data_param,
        data_value,
        expected_call_kwargs,
    ):
        """Test successful POST request with JSON or form data"""
        mock_client = AsyncMock()
        client._client = mock_client
        mock_client.post.return_value = mock_response(json_data={"result": "success"})

        kwargs = {data_param: data_value}
        result = await client._request(method, endpoint="/test", **kwargs)
        assert result == {"result": "success"}
        mock_client.post.assert_called_once_with(
            "https://api.example.com/test", **expected_call_kwargs
        )


class TestBaseAPIClientFormatResponse:
    """Test format_response method"""

    @pytest.fixture
    def client(self, base_url, api_name):
        """Create a test client"""
        return ConcreteAPIClient(base_url=base_url, api_name=api_name)

    @pytest.mark.parametrize(
        "data,metadata,expected",
        [
            (
                {"data": "test"},
                {"count": 1},
                {"data": {"data": "test"}, "metadata": {"count": 1}},
            ),
            ({"data": "test"}, None, {"data": "test"}),
            ([1, 2, 3], None, [1, 2, 3]),
            ("text", None, "text"),
        ],
    )
    def test_format_response(self, client, data, metadata, expected):
        """Test formatting response with various data types and metadata"""
        result = client.format_response(data, metadata=metadata)
        assert result == expected


class TestBaseAPIClientClose:
    """Test close method"""

    @pytest.mark.asyncio
    async def test_close(self, base_url, api_name):
        """Test closing client"""
        client = ConcreteAPIClient(base_url=base_url, api_name=api_name, enable_cache=False)
        mock_client = AsyncMock()
        client._client = mock_client

        await client.close()
        mock_client.aclose.assert_called_once()
        assert client._client is None

    @pytest.mark.asyncio
    async def test_close_no_client(self, base_url, api_name):
        """Test closing when no client exists"""
        client = ConcreteAPIClient(base_url=base_url, api_name=api_name)
        await client.close()  # Should not raise
        assert client._client is None
